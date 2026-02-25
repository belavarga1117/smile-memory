"""Admin configuration for the import pipeline."""

from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html

from .models import ImportJob, ImportLog
from .pipeline import ImportPipeline


class ImportLogInline(admin.TabularInline):
    model = ImportLog
    extra = 0
    readonly_fields = ("row_number", "level_badge", "message", "created_at")
    fields = ("row_number", "level_badge", "message", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Level")
    def level_badge(self, obj):
        colors = {
            "success": "#16a34a",
            "info": "#2563eb",
            "warning": "#d97706",
            "error": "#dc2626",
        }
        color = colors.get(obj.level, "#6b7280")
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
            color,
            obj.get_level_display(),
        )


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    change_list_template = "admin/importer/importjob/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "sync/<str:source>/",
                self.admin_site.admin_view(self.sync_view),
                name="importer_run_sync",
            ),
        ]
        return custom + urls

    def sync_view(self, request, source):
        from .tasks import sync_all_tours

        if request.method != "POST":
            return redirect("..")

        sources = None if source == "all" else [source]
        result = sync_all_tours.delay(sources=sources)
        label = "all sources" if sources is None else source
        self.message_user(
            request,
            f"✅ Sync queued ({label}). Task ID: {result.id} — check worker logs for progress.",
            messages.SUCCESS,
        )
        return redirect("..")

    list_display = (
        "name",
        "source",
        "file_format",
        "status_badge",
        "total_rows",
        "rows_created",
        "rows_updated",
        "rows_failed",
        "success_rate_display",
        "imported_by",
        "created_at",
    )
    list_filter = ("status", "source", "file_format", "created_at")
    search_fields = ("name",)
    readonly_fields = (
        "id",
        "status",
        "total_rows",
        "rows_created",
        "rows_updated",
        "rows_skipped",
        "rows_failed",
        "error_message",
        "parsed_headers_display",
        "parsed_preview_display",
        "field_mapping_display",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
    )
    inlines = [ImportLogInline]
    actions = ["action_run_import", "action_preview"]

    fieldsets = (
        (
            "Import Setup",
            {
                "fields": (
                    "name",
                    "source",
                    "file_format",
                    "uploaded_file",
                    "source_url",
                ),
            },
        ),
        (
            "Field Mapping",
            {
                "fields": ("field_mapping", "field_mapping_display"),
                "description": (
                    "Optional: manually map source columns to Tour fields. "
                    'Format: {"source_column": "tour_field"}. '
                    "Leave empty for auto-detection."
                ),
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "status",
                    "total_rows",
                    "rows_created",
                    "rows_updated",
                    "rows_skipped",
                    "rows_failed",
                    "error_message",
                ),
            },
        ),
        (
            "Preview",
            {
                "classes": ("collapse",),
                "fields": ("parsed_headers_display", "parsed_preview_display"),
            },
        ),
        (
            "Metadata",
            {
                "classes": ("collapse",),
                "fields": (
                    "id",
                    "imported_by",
                    "started_at",
                    "completed_at",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#6b7280",
            "parsing": "#2563eb",
            "mapping": "#2563eb",
            "importing": "#d97706",
            "completed": "#16a34a",
            "failed": "#dc2626",
            "partial": "#d97706",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:#fff; padding:2px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Success %")
    def success_rate_display(self, obj):
        rate = obj.success_rate
        if obj.total_rows == 0:
            return "—"
        color = "#16a34a" if rate >= 90 else "#d97706" if rate >= 50 else "#dc2626"
        return format_html('<span style="color:{}">{}</span>', color, f"{rate:.0f}%")

    @admin.display(description="Detected Headers")
    def parsed_headers_display(self, obj):
        if not obj.parsed_headers:
            return "—"
        items = ", ".join(obj.parsed_headers)
        return format_html("<code>{}</code>", items)

    @admin.display(description="Data Preview (first rows)")
    def parsed_preview_display(self, obj):
        if not obj.parsed_preview:
            return "—"
        rows_html = ""
        for i, row in enumerate(obj.parsed_preview[:5], 1):
            items = "; ".join(f"{k}: {v}" for k, v in row.items() if v)
            rows_html += f"<div style='margin-bottom:4px;'><strong>Row {i}:</strong> {items}</div>"
        return format_html(rows_html)

    @admin.display(description="Active Mapping")
    def field_mapping_display(self, obj):
        if not obj.field_mapping:
            return "Auto-detect (no mapping set)"
        items = "<br>".join(
            f"<code>{k}</code> → <code>{v}</code>" for k, v in obj.field_mapping.items()
        )
        return format_html(items)

    @admin.action(description="Run import (parse + create/update tours)")
    def action_run_import(self, request, queryset):
        for job in queryset:
            if job.status not in (
                ImportJob.Status.PENDING,
                ImportJob.Status.FAILED,
                ImportJob.Status.PARTIAL,
            ):
                messages.warning(
                    request, f"Skipped {job.name}: status is {job.get_status_display()}"
                )
                continue
            job.imported_by = request.user
            job.save(update_fields=["imported_by"])
            pipeline = ImportPipeline(job)
            pipeline.run()
            messages.success(
                request,
                f"{job.name}: {job.rows_created} created, {job.rows_updated} updated, "
                f"{job.rows_failed} failed ({job.get_status_display()})",
            )

    @admin.action(description="Preview only (parse file, don't import)")
    def action_preview(self, request, queryset):
        for job in queryset:
            job.imported_by = request.user
            job.save(update_fields=["imported_by"])
            pipeline = ImportPipeline(job)
            pipeline.preview_only()
            if job.status == ImportJob.Status.FAILED:
                messages.error(request, f"{job.name}: {job.error_message}")
            else:
                messages.success(
                    request,
                    f"{job.name}: Parsed {job.total_rows} rows. "
                    f"Headers: {', '.join(job.parsed_headers[:10])}. "
                    f"Review the preview below, then run import.",
                )

    def save_model(self, request, obj, form, change):
        if not obj.imported_by:
            obj.imported_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ("job", "row_number", "level", "message_short", "created_at")
    list_filter = ("level", "job__source")
    search_fields = ("message",)
    readonly_fields = (
        "job",
        "row_number",
        "level",
        "message",
        "raw_data",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    @admin.display(description="Message")
    def message_short(self, obj):
        return obj.message[:120] + "..." if len(obj.message) > 120 else obj.message
