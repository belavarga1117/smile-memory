from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "phone",
        "marketing_opt_in",
        "total_inquiries",
        "total_bookings",
        "created_at",
    ]
    list_filter = ["marketing_opt_in", "created_at"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    readonly_fields = ["total_inquiries", "total_bookings", "created_at", "updated_at"]
    fieldsets = (
        (
            None,
            {
                "fields": ("email", "first_name", "last_name", "phone", "line_id"),
            },
        ),
        (
            "Marketing",
            {
                "fields": ("marketing_opt_in", "opted_in_at", "tags"),
            },
        ),
        (
            "Stats",
            {
                "fields": ("total_inquiries", "total_bookings", "notes"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
