"""Tests for tours DRF API endpoints."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestTourAPI:
    def test_list_tours(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_list_only_published(self, api_client, tour, draft_tour):
        resp = api_client.get("/api/v1/tours/")
        slugs = [t["slug"] for t in resp.data["results"]]
        assert tour.slug in slugs
        assert draft_tour.slug not in slugs

    def test_retrieve_tour(self, api_client, tour):
        resp = api_client.get(f"/api/v1/tours/{tour.pk}/")
        assert resp.status_code == 200
        assert resp.data["title"] == "Tokyo Explorer"
        assert resp.data["slug"] == "tokyo-explorer"

    def test_retrieve_draft_404(self, api_client, draft_tour):
        resp = api_client.get(f"/api/v1/tours/{draft_tour.pk}/")
        assert resp.status_code == 404

    def test_filter_by_destination(self, api_client, tour, destination):
        resp = api_client.get("/api/v1/tours/", {"destination": "japan"})
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_filter_by_category(self, api_client, tour, category):
        resp = api_client.get("/api/v1/tours/", {"category": "beach"})
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_filter_by_min_price(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"min_price": "20000"})
        assert resp.data["count"] >= 1

    def test_filter_by_max_price(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"max_price": "50000"})
        assert resp.data["count"] >= 1

    def test_filter_by_max_price_excludes(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"max_price": "100"})
        assert resp.data["count"] == 0

    def test_search(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"search": "Tokyo"})
        assert resp.data["count"] >= 1

    def test_search_no_match(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"search": "xyznonexistent"})
        assert resp.data["count"] == 0

    def test_ordering_price_asc(self, api_client, tour):
        resp = api_client.get("/api/v1/tours/", {"ordering": "price_from"})
        assert resp.status_code == 200

    def test_detail_includes_nested(
        self, api_client, tour, itinerary_day, price_option
    ):
        resp = api_client.get(f"/api/v1/tours/{tour.pk}/")
        assert "itinerary_days" in resp.data
        assert "price_options" in resp.data
        assert "destinations" in resp.data
        assert "categories" in resp.data

    def test_read_only(self, api_client, tour):
        resp = api_client.post("/api/v1/tours/", {"title": "Hack"})
        assert resp.status_code == 405  # Method Not Allowed

    def test_delete_not_allowed(self, api_client, tour):
        resp = api_client.delete(f"/api/v1/tours/{tour.pk}/")
        assert resp.status_code == 405


@pytest.mark.django_db
class TestDestinationAPI:
    def test_list_destinations(self, api_client, destination):
        resp = api_client.get("/api/v1/destinations/")
        assert resp.status_code == 200

    def test_retrieve_destination(self, api_client, destination):
        resp = api_client.get(f"/api/v1/destinations/{destination.pk}/")
        assert resp.status_code == 200
        assert resp.data["name"] == "Japan"


@pytest.mark.django_db
class TestCategoryAPI:
    def test_list_categories(self, api_client, category):
        resp = api_client.get("/api/v1/categories/")
        assert resp.status_code == 200

    def test_retrieve_category(self, api_client, category):
        resp = api_client.get(f"/api/v1/categories/{category.pk}/")
        assert resp.status_code == 200
        assert resp.data["name"] == "Beach"
