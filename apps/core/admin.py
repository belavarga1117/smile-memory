from django.contrib import admin

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ("General", {"fields": ("site_name", "admin_email", "phone_number")}),
        (
            "Social / Messaging",
            {"fields": ("whatsapp_number", "line_id", "facebook_url", "instagram_url")},
        ),
        ("Address", {"fields": ("address", "address_th")}),
        ("SEO", {"fields": ("meta_description", "meta_description_th")}),
        ("Payment Info", {"fields": ("bank_account_info", "bank_account_info_th")}),
    )

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
