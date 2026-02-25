from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Inquiry, InquiryNote


class InquiryNoteInline(admin.TabularInline):
    model = InquiryNote
    extra = 1
    readonly_fields = ["created_at"]
    fields = ["note", "author", "is_email_sent", "created_at"]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = [
        "reference_number",
        "contact_name",
        "tour_display",
        "status_badge",
        "num_adults",
        "quoted_price",
        "assigned_to",
        "created_at",
    ]
    list_filter = ["status", "created_at", "assigned_to"]
    search_fields = [
        "reference_number",
        "contact_name",
        "contact_email",
        "tour__title",
        "customer__email",
    ]
    list_editable = ["assigned_to"]
    readonly_fields = [
        "reference_number",
        "customer",
        "created_at",
        "updated_at",
        "confirmed_at",
        "rejected_at",
    ]
    raw_id_fields = ["tour", "departure", "customer"]
    inlines = [InquiryNoteInline]
    actions = ["action_confirm", "action_reject", "action_mark_contacted"]

    fieldsets = (
        (
            "Inquiry",
            {
                "fields": (
                    "reference_number",
                    "status",
                    "assigned_to",
                    "customer",
                    "tour",
                    "departure",
                ),
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "contact_name",
                    "contact_email",
                    "contact_phone",
                    "marketing_opt_in",
                ),
            },
        ),
        (
            "Travel Details",
            {
                "fields": (
                    "num_adults",
                    "num_children",
                    "num_infants",
                    "room_preference",
                    "special_requests",
                ),
            },
        ),
        (
            "Pricing (filled by admin)",
            {
                "fields": ("quoted_price", "deposit_amount"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "confirmed_at", "rejected_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def tour_display(self, obj):
        if obj.tour:
            return obj.tour.title[:50]
        return "—"

    tour_display.short_description = "Tour"

    def status_badge(self, obj):
        colors = {
            "new": "#3b82f6",
            "contacted": "#f59e0b",
            "confirmed": "#10b981",
            "rejected": "#ef4444",
            "cancelled": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; '
            'border-radius:10px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    @admin.action(description="✅ Mark as Confirmed + send confirmation email")
    def action_confirm(self, request, queryset):
        from .notifications import send_booking_confirmation

        count = 0
        for inquiry in queryset.filter(status__in=["new", "contacted"]):
            inquiry.status = Inquiry.Status.CONFIRMED
            inquiry.confirmed_at = timezone.now()
            inquiry.save(update_fields=["status", "confirmed_at"])
            try:
                send_booking_confirmation(inquiry)
            except Exception:
                pass  # logged inside send_booking_confirmation
            count += 1
        self.message_user(request, f"{count} inquiry(ies) confirmed and emailed.")

    @admin.action(description="❌ Mark as Rejected + send rejection email")
    def action_reject(self, request, queryset):
        from .notifications import send_booking_rejection

        count = 0
        for inquiry in queryset.filter(status__in=["new", "contacted"]):
            inquiry.status = Inquiry.Status.REJECTED
            inquiry.rejected_at = timezone.now()
            inquiry.save(update_fields=["status", "rejected_at"])
            try:
                send_booking_rejection(inquiry)
            except Exception:
                pass  # logged inside send_booking_rejection
            count += 1
        self.message_user(request, f"{count} inquiry(ies) rejected and emailed.")

    @admin.action(description="Mark as Contacted")
    def action_mark_contacted(self, request, queryset):
        count = queryset.filter(status="new").update(status=Inquiry.Status.CONTACTED)
        self.message_user(request, f"{count} inquiry(ies) marked as contacted.")


@admin.register(InquiryNote)
class InquiryNoteAdmin(admin.ModelAdmin):
    list_display = ["inquiry", "author", "is_email_sent", "created_at"]
    list_filter = ["is_email_sent", "created_at"]
