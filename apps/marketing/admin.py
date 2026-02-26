from django.contrib import admin
from django.http import HttpResponse
from django.template import Context, Template
from django.utils.html import format_html

from .models import Campaign, CampaignRecipient, EmailTemplate, Subscriber


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "subject", "subject_th", "updated_at"]
    search_fields = ["name", "subject"]
    fieldsets = (
        (None, {"fields": ("name",)}),
        ("English", {"fields": ("subject", "body_html", "body_text")}),
        ("Thai", {"fields": ("subject_th",)}),
    )


class CampaignRecipientInline(admin.TabularInline):
    model = CampaignRecipient
    extra = 0
    readonly_fields = ["customer", "status", "sent_at", "error_message"]
    can_delete = False

    def has_add_permission(self, _request, _obj=None):
        return False


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "status_badge",
        "recipient_count_display",
        "total_sent",
        "total_failed",
        "sent_at",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["name", "subject"]
    readonly_fields = [
        "total_recipients",
        "total_sent",
        "total_failed",
        "sent_at",
        "created_at",
        "updated_at",
    ]
    inlines = [CampaignRecipientInline]
    actions = ["action_send_campaign", "action_preview_campaign"]

    fieldsets = (
        (
            None,
            {"fields": ("name", "status", "template")},
        ),
        (
            "Content (if not using template)",
            {
                "fields": ("subject", "subject_th", "body_html", "body_text"),
                "classes": ("collapse",),
            },
        ),
        (
            "Targeting",
            {"fields": ("send_to_all_opted_in", "customer_tags")},
        ),
        (
            "Scheduling",
            {"fields": ("scheduled_at", "sent_by")},
        ),
        (
            "Stats",
            {
                "fields": (
                    "total_recipients",
                    "total_sent",
                    "total_failed",
                    "sent_at",
                ),
            },
        ),
    )

    def status_badge(self, obj):
        colors = {
            "draft": "#6b7280",
            "scheduled": "#f59e0b",
            "sending": "#3b82f6",
            "sent": "#10b981",
            "cancelled": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{}; color:white; padding:3px 8px; '
            'border-radius:10px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def recipient_count_display(self, obj):
        from .tasks import _collect_recipients

        if obj.status == Campaign.Status.DRAFT:
            count = len(_collect_recipients(obj))
            return format_html(
                "<span title='estimated before send'>{} 📧</span>", count
            )
        return obj.total_recipients

    recipient_count_display.short_description = "Recipients"

    @admin.action(description="✉ Send selected campaigns")
    def action_send_campaign(self, request, queryset):
        from .tasks import send_campaign

        sent = 0
        for campaign in queryset.filter(status=Campaign.Status.DRAFT):
            send_campaign(campaign.pk, sent_by=request.user)
            sent += 1
        if sent:
            self.message_user(request, f"{sent} campaign(s) sent.")
        else:
            self.message_user(
                request,
                "No DRAFT campaigns selected (only draft campaigns can be sent).",
                level="warning",
            )

    @admin.action(description="👁 Preview campaign HTML")
    def action_preview_campaign(self, request, queryset):
        campaign = queryset.first()
        if not campaign:
            return
        body_html = campaign.get_effective_body_html()
        subject = campaign.get_effective_subject()
        preview_html = Template(body_html).render(
            Context(
                {
                    "customer": None,
                    "email": "preview@example.com",
                    "site_name": "Smile Memory",
                    "site_url": "https://smilememorytravel.com",
                    "unsubscribe_url": "https://smilememorytravel.com/th/newsletter/unsubscribe/",
                }
            )
        )
        return HttpResponse(
            f"<h2 style='font-family:sans-serif; padding:16px'>Preview: {subject}</h2>"
            + preview_html
        )


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "is_active",
        "is_confirmed",
        "language",
        "source",
        "customer",
        "created_at",
    ]
    list_filter = ["is_active", "is_confirmed", "language", "source", "created_at"]
    search_fields = ["email"]
    readonly_fields = [
        "confirmation_token",
        "confirmed_at",
        "unsubscribe_token",
        "created_at",
    ]
    actions = ["action_reactivate", "action_deactivate"]

    @admin.action(description="Reactivate selected subscribers")
    def action_reactivate(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} subscriber(s) reactivated.")

    @admin.action(description="Deactivate (unsubscribe) selected")
    def action_deactivate(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} subscriber(s) deactivated.")
