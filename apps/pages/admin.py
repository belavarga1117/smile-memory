from django.contrib import admin

from .models import ContactMessage, FAQ, HeroSlide, Testimonial, TrustBadge


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["name", "tour_name", "rating", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active", "rating"]


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    list_display = ["value", "label", "sort_order"]
    list_editable = ["sort_order"]


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["is_active"]


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    readonly_fields = ["name", "email", "phone", "subject", "message", "created_at"]
    search_fields = ["name", "email", "subject"]

    def has_add_permission(self, request):
        return False
