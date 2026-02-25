from rest_framework import serializers

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


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            "id",
            "name",
            "name_th",
            "slug",
            "country_code_iso2",
            "country_code_iso3",
            "image",
            "is_featured",
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "name_th", "slug", "icon"]


class AirlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airline
        fields = ["id", "code", "name", "name_th"]


class TourImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TourImage
        fields = ["id", "image", "image_url", "caption", "caption_th", "sort_order"]


class ItineraryDaySerializer(serializers.ModelSerializer):
    meals_display = serializers.ReadOnlyField()

    class Meta:
        model = ItineraryDay
        fields = [
            "id",
            "day_number",
            "title",
            "title_th",
            "description",
            "description_th",
            "breakfast",
            "breakfast_description",
            "lunch",
            "lunch_description",
            "dinner",
            "dinner_description",
            "hotel_name",
            "hotel_stars",
            "meals_display",
        ]


class PriceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceOption
        fields = ["id", "name", "name_th", "price", "currency", "description"]


class TourFlightSerializer(serializers.ModelSerializer):
    airline = AirlineSerializer(read_only=True)

    class Meta:
        model = TourFlight
        fields = [
            "id",
            "airline",
            "flight_number",
            "route",
            "departure_time",
            "arrival_time",
        ]


class TourDepartureSerializer(serializers.ModelSerializer):
    effective_price = serializers.ReadOnlyField()
    has_promo = serializers.ReadOnlyField()
    flights = TourFlightSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = TourDeparture
        fields = [
            "id",
            "period_code",
            "departure_date",
            "return_date",
            "departure_airport",
            "group_size",
            "seats_available",
            "status",
            "status_display",
            "price_adult",
            "price_child",
            "price_child_no_bed",
            "price_infant",
            "price_join_land",
            "price_single_supplement",
            "price_adult_promo",
            "effective_price",
            "has_promo",
            "deposit",
            "flights",
        ]


class TourListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for tour list/cards."""

    destinations = DestinationSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    airline = AirlineSerializer(read_only=True)
    duration_display = serializers.ReadOnlyField()
    hotel_stars_display = serializers.ReadOnlyField()
    url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Tour
        fields = [
            "id",
            "title",
            "title_th",
            "slug",
            "short_description",
            "short_description_th",
            "destinations",
            "categories",
            "airline",
            "price_from",
            "currency",
            "duration_days",
            "duration_nights",
            "duration_display",
            "hotel_stars_min",
            "hotel_stars_max",
            "hotel_stars_display",
            "total_meals",
            "is_featured",
            "thumbnail",
            "hero_image",
            "hero_image_url",
            "url",
        ]


class TourDetailSerializer(serializers.ModelSerializer):
    """Full serializer for tour detail page."""

    destinations = DestinationSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    airline = AirlineSerializer(read_only=True)
    images = TourImageSerializer(many=True, read_only=True)
    itinerary_days = ItineraryDaySerializer(many=True, read_only=True)
    price_options = PriceOptionSerializer(many=True, read_only=True)
    departures = TourDepartureSerializer(many=True, read_only=True)
    duration_display = serializers.ReadOnlyField()
    hotel_stars_display = serializers.ReadOnlyField()

    class Meta:
        model = Tour
        fields = [
            "id",
            "title",
            "title_th",
            "slug",
            "highlight",
            "highlight_th",
            "description",
            "description_th",
            "short_description",
            "short_description_th",
            "destinations",
            "locations",
            "categories",
            "airline",
            "price_from",
            "currency",
            "duration_days",
            "duration_nights",
            "duration_display",
            "hotel_stars_min",
            "hotel_stars_max",
            "hotel_stars_display",
            "plane_meals",
            "total_meals",
            "includes",
            "includes_th",
            "excludes",
            "excludes_th",
            "hero_image",
            "hero_image_url",
            "thumbnail",
            "pdf_file",
            "pdf_url",
            "is_featured",
            "images",
            "itinerary_days",
            "price_options",
            "departures",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
