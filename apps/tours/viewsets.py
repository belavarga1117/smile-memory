from django.db.models import Exists, OuterRef
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Category, Destination, Tour, TourDeparture
from .serializers import (
    CategorySerializer,
    DestinationSerializer,
    TourDetailSerializer,
    TourListSerializer,
)


class TourFilter(filters.FilterSet):
    destination = filters.CharFilter(field_name="destinations__slug")
    category = filters.CharFilter(field_name="categories__slug")
    min_price = filters.NumberFilter(field_name="price_from", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="price_from", lookup_expr="lte")
    max_duration = filters.NumberFilter(field_name="duration_days", lookup_expr="lte")

    class Meta:
        model = Tour
        fields = [
            "destination",
            "category",
            "min_price",
            "max_price",
            "max_duration",
        ]


class TourViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    filterset_class = TourFilter
    search_fields = ["title", "title_th", "description"]
    ordering_fields = ["price_from", "created_at", "duration_days"]
    ordering = ["-is_featured", "-created_at"]

    def get_queryset(self):
        qs = (
            Tour.objects.filter(status=Tour.Status.PUBLISHED)
            .filter(
                Exists(
                    TourDeparture.objects.filter(
                        tour=OuterRef("pk"), status="available"
                    )
                )
            )
            .select_related("airline")
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "destinations",
                "categories",
                "images",
                "itinerary_days",
                "price_options",
            )
        else:
            qs = qs.prefetch_related("destinations", "categories")
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TourDetailSerializer
        return TourListSerializer


class DestinationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [AllowAny]
    search_fields = ["name", "name_th"]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
