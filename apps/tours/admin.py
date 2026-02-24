from django.contrib import admin

from .models import (
    Airline,
    Category,
    Destination,
    ItineraryDay,
    PriceOption,
    Tour,
    TourDeparture,
    TourFlight,
    TourImage,
)


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "name_th",
        "country_code_iso3",
        "parent",
        "is_featured",
        "sort_order",
    )
    list_editable = ("is_featured", "sort_order")
    list_filter = ("is_featured", "parent")
    search_fields = ("name", "name_th", "country_code_iso2", "country_code_iso3")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "name_th", "icon", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


# --- Tour inlines ---


class TourImageInline(admin.TabularInline):
    model = TourImage
    extra = 1
    fields = ("image", "image_url", "caption", "caption_th", "sort_order")


class ItineraryDayInline(admin.StackedInline):
    model = ItineraryDay
    extra = 0
    fields = (
        "day_number",
        ("title", "title_th"),
        ("description", "description_th"),
        ("breakfast", "breakfast_description"),
        ("lunch", "lunch_description"),
        ("dinner", "dinner_description"),
        ("hotel_name", "hotel_stars"),
    )


class PriceOptionInline(admin.TabularInline):
    model = PriceOption
    extra = 1
    fields = ("name", "name_th", "price", "currency", "description", "sort_order")


class TourFlightInline(admin.TabularInline):
    model = TourFlight
    fk_name = "departure"
    extra = 0
    fields = (
        "airline",
        "flight_number",
        "route",
        "departure_time",
        "arrival_time",
        "sort_order",
    )


class TourDepartureInline(admin.TabularInline):
    model = TourDeparture
    extra = 0
    fields = (
        "departure_date",
        "return_date",
        "status",
        "group_size",
        "seats_available",
        "price_adult",
        "price_adult_promo",
        "deposit",
        "departure_airport",
        "period_code",
    )
    readonly_fields = ("booked",)
    show_change_link = True


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product_code",
        "status",
        "is_featured",
        "price_from",
        "currency",
        "duration_display",
        "airline",
        "source",
        "updated_at",
    )
    list_filter = ("status", "is_featured", "categories", "source", "airline")
    list_editable = ("status", "is_featured")
    search_fields = ("title", "title_th", "product_code", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("destinations", "categories")
    readonly_fields = ("created_at", "updated_at", "last_synced_at")
    inlines = [
        TourDepartureInline,
        TourImageInline,
        ItineraryDayInline,
        PriceOptionInline,
    ]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("title", "title_th"),
                    ("slug", "product_code"),
                    ("highlight", "highlight_th"),
                    ("short_description", "short_description_th"),
                    ("description", "description_th"),
                )
            },
        ),
        (
            "Classification",
            {
                "fields": (
                    "destinations",
                    "locations",
                    "categories",
                    ("status", "is_featured"),
                    "airline",
                )
            },
        ),
        (
            "Pricing",
            {"fields": (("price_from", "currency"),)},
        ),
        (
            "Details",
            {
                "fields": (
                    ("duration_days", "duration_nights"),
                    ("hotel_stars_min", "hotel_stars_max"),
                    ("plane_meals", "total_meals"),
                    ("includes", "includes_th"),
                    ("excludes", "excludes_th"),
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    ("hero_image", "hero_image_url"),
                    "thumbnail",
                    ("pdf_file", "pdf_url"),
                    "word_url",
                )
            },
        ),
        (
            "Import Source",
            {
                "classes": ("collapse",),
                "fields": ("source", "external_id", "source_url", "last_synced_at"),
            },
        ),
        (
            "SEO",
            {
                "classes": ("collapse",),
                "fields": ("meta_title", "meta_description"),
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Duration")
    def duration_display(self, obj):
        return obj.duration_display


@admin.register(TourDeparture)
class TourDepartureAdmin(admin.ModelAdmin):
    list_display = (
        "tour",
        "departure_date",
        "return_date",
        "status",
        "price_adult",
        "price_adult_promo",
        "seats_available",
        "group_size",
    )
    list_filter = ("status", "departure_date")
    search_fields = ("tour__title", "period_code")
    inlines = [TourFlightInline]
    readonly_fields = ("created_at", "updated_at")
