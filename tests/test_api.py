"""API integration tests for Tour, Destination, Category endpoints."""

from decimal import Decimal

import pytest

from apps.tours.models import Tour

from .factories import (
    CategoryFactory,
    DestinationFactory,
    TourDepartureFactory,
    TourFactory,
    TourImageFactory,
    ItineraryDayFactory,
)


@pytest.mark.django_db
class TestTourListAPI:
    """Test /api/v1/tours/ endpoint with filters."""

    def _url(self):
        return "/api/v1/tours/"

    def test_list_returns_200(self, client):
        TourFactory()
        resp = client.get(self._url())
        assert resp.status_code == 200

    def test_only_published_tours(self, client):
        TourFactory(title="Published Tour", status=Tour.Status.PUBLISHED)
        TourFactory(title="Draft Tour", status=Tour.Status.DRAFT)
        TourFactory(title="Archived Tour", status=Tour.Status.ARCHIVED)

        resp = client.get(self._url())
        data = resp.json()
        titles = [t["title"] for t in data["results"]]
        assert "Published Tour" in titles
        assert "Draft Tour" not in titles
        assert "Archived Tour" not in titles

    def test_filter_by_destination(self, client):
        japan = DestinationFactory(name="Japan", slug="japan")
        korea = DestinationFactory(name="Korea", slug="korea")
        TourFactory(title="Japan Tour", destinations=[japan])
        TourFactory(title="Korea Tour", destinations=[korea])

        resp = client.get(self._url(), {"destination": "japan"})
        data = resp.json()
        titles = [t["title"] for t in data["results"]]
        assert "Japan Tour" in titles
        assert "Korea Tour" not in titles

    def test_filter_by_category(self, client):
        beach = CategoryFactory(name="Beach", slug="beach")
        culture = CategoryFactory(name="Culture", slug="culture")
        TourFactory(title="Beach Tour", categories=[beach])
        TourFactory(title="Culture Tour", categories=[culture])

        resp = client.get(self._url(), {"category": "beach"})
        data = resp.json()
        titles = [t["title"] for t in data["results"]]
        assert "Beach Tour" in titles
        assert "Culture Tour" not in titles

    def test_filter_by_price_range(self, client):
        TourFactory(title="Cheap", price_from=Decimal("10000"))
        TourFactory(title="Expensive", price_from=Decimal("80000"))

        resp = client.get(self._url(), {"min_price": 5000, "max_price": 30000})
        data = resp.json()
        titles = [t["title"] for t in data["results"]]
        assert "Cheap" in titles
        assert "Expensive" not in titles

    def test_search_by_title(self, client):
        TourFactory(title="Tokyo Adventure")
        TourFactory(title="Seoul Explorer")

        resp = client.get(self._url(), {"search": "Tokyo"})
        data = resp.json()
        titles = [t["title"] for t in data["results"]]
        assert "Tokyo Adventure" in titles
        assert "Seoul Explorer" not in titles

    def test_product_code_not_searchable(self, client):
        # product_code is hidden from public API — not in search_fields
        TourFactory(product_code="ZGTYO-999", title="Generic Tour Title")

        resp = client.get(self._url(), {"search": "ZGTYO-999"})
        data = resp.json()
        assert data["count"] == 0


@pytest.mark.django_db
class TestTourDetailAPI:
    """Test /api/v1/tours/{id}/ endpoint with nested relations."""

    def test_detail_returns_200(self, client):
        tour = TourFactory()
        resp = client.get(f"/api/v1/tours/{tour.pk}/")
        assert resp.status_code == 200

    def test_detail_includes_departures(self, client):
        tour = TourFactory(with_departure=False)
        TourDepartureFactory(tour=tour)
        TourDepartureFactory(tour=tour)

        resp = client.get(f"/api/v1/tours/{tour.pk}/")
        data = resp.json()
        assert "departures" in data
        assert len(data["departures"]) == 2

    def test_detail_includes_itinerary(self, client):
        tour = TourFactory()
        ItineraryDayFactory(tour=tour, day_number=1)
        ItineraryDayFactory(tour=tour, day_number=2)

        resp = client.get(f"/api/v1/tours/{tour.pk}/")
        data = resp.json()
        assert "itinerary_days" in data
        assert len(data["itinerary_days"]) == 2

    def test_detail_includes_images(self, client):
        tour = TourFactory()
        TourImageFactory(tour=tour)

        resp = client.get(f"/api/v1/tours/{tour.pk}/")
        data = resp.json()
        assert "images" in data
        assert len(data["images"]) == 1

    def test_draft_tour_not_accessible(self, client):
        tour = TourFactory(status=Tour.Status.DRAFT)
        resp = client.get(f"/api/v1/tours/{tour.pk}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestDestinationAPI:
    def test_list_destinations(self, client):
        DestinationFactory(name="Japan")
        DestinationFactory(name="Korea")
        resp = client.get("/api/v1/destinations/")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 2


@pytest.mark.django_db
class TestCategoryAPI:
    def test_list_categories(self, client):
        CategoryFactory(name="Beach")
        resp = client.get("/api/v1/categories/")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1
