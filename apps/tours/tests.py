"""Tests for tours app — models, views, API."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.tours.models import (
    Destination,
    ItineraryDay,
    Tour,
    TourDeparture,
)


# ── Model Tests ──


class TestDestinationModel:
    def test_str(self, destination):
        assert str(destination) == "Japan"

    def test_auto_slug(self, db):
        d = Destination(name="South Korea")
        d.save()
        assert d.slug == "south-korea"

    def test_ordering(self, db):
        d1 = Destination.objects.create(name="B Dest", slug="b-dest", sort_order=2)
        d2 = Destination.objects.create(name="A Dest", slug="a-dest", sort_order=1)
        qs = Destination.objects.filter(pk__in=[d1.pk, d2.pk])
        assert list(qs) == [d2, d1]


class TestCategoryModel:
    def test_str(self, category):
        assert str(category) == "Beach"


class TestAirlineModel:
    def test_str(self, airline):
        assert str(airline) == "TG — Thai Airways"


class TestTourModel:
    def test_str(self, tour):
        assert str(tour) == "Tokyo Explorer"

    def test_get_absolute_url(self, tour):
        assert tour.get_absolute_url() == reverse(
            "tours:detail", kwargs={"slug": "tokyo-explorer"}
        )

    def test_auto_slug(self, db):
        t = Tour(title="My Amazing Tour", status=Tour.Status.DRAFT)
        t.save()
        assert t.slug == "my-amazing-tour"

    def test_duration_display(self, tour):
        assert tour.duration_display == "5D/4N"

    def test_duration_display_days_only(self, db):
        t = Tour.objects.create(
            title="Test", slug="test-dur", duration_days=3, duration_nights=None
        )
        assert t.duration_display == "3 days"

    def test_duration_display_empty(self, db):
        t = Tour.objects.create(title="Test", slug="test-dur-empty")
        assert t.duration_display == ""

    def test_hotel_stars_display_same(self, tour):
        assert tour.hotel_stars_display == "4-star"

    def test_hotel_stars_display_range(self, db):
        t = Tour.objects.create(
            title="Range", slug="range", hotel_stars_min=3, hotel_stars_max=5
        )
        assert t.hotel_stars_display == "3-5 star"

    def test_hotel_stars_display_empty(self, db):
        t = Tour.objects.create(title="Empty", slug="empty-stars")
        assert t.hotel_stars_display == ""

    def test_update_price_from(self, tour):
        TourDeparture.objects.create(
            tour=tour,
            departure_date=date.today() + timedelta(days=60),
            return_date=date.today() + timedelta(days=64),
            price_adult=Decimal("19900.00"),
            status=TourDeparture.PeriodStatus.AVAILABLE,
        )
        tour.update_price_from()
        tour.refresh_from_db()
        assert tour.price_from == Decimal("19900.00")

    def test_status_choices(self):
        assert Tour.Status.DRAFT == "draft"
        assert Tour.Status.PUBLISHED == "published"
        assert Tour.Status.ARCHIVED == "archived"


class TestTourDepartureModel:
    def test_str(self, departure):
        assert "Tokyo Explorer" in str(departure)
        assert "Available" in str(departure)

    def test_effective_price_regular(self, departure):
        assert departure.effective_price == Decimal("29900.00")

    def test_effective_price_promo(self, departure):
        departure.price_adult_promo = Decimal("24900.00")
        departure.save()
        assert departure.effective_price == Decimal("24900.00")

    def test_has_promo_true(self, departure):
        departure.price_adult_promo = Decimal("24900.00")
        departure.save()
        assert departure.has_promo is True

    def test_has_promo_false(self, departure):
        assert departure.has_promo is False

    def test_has_promo_false_when_higher(self, departure):
        departure.price_adult_promo = Decimal("39900.00")
        departure.save()
        assert departure.has_promo is False


class TestItineraryDayModel:
    def test_str(self, itinerary_day):
        assert str(itinerary_day) == "Day 1: Bangkok to Tokyo"

    def test_meals_display(self, itinerary_day):
        assert itinerary_day.meals_display == "B, L, D"

    def test_meals_display_partial(self, db, tour):
        day = ItineraryDay.objects.create(
            tour=tour,
            day_number=2,
            title="Day 2",
            description="Explore",
            breakfast="Y",
            lunch="N",
            dinner="Y",
        )
        assert day.meals_display == "B, D"

    def test_meals_display_none(self, db, tour):
        day = ItineraryDay.objects.create(
            tour=tour,
            day_number=3,
            title="Day 3",
            description="Free day",
            breakfast="N",
            lunch="N",
            dinner="N",
        )
        assert day.meals_display == ""


class TestTourImageModel:
    def test_str(self, tour_image):
        assert "Tokyo Explorer" in str(tour_image)


class TestPriceOptionModel:
    def test_str(self, price_option):
        assert "Adult Double" in str(price_option)
        assert "29900" in str(price_option)


# ── View Tests ──


@pytest.mark.django_db
class TestTourListView:
    def test_tour_list_200(self, client, tour):
        resp = client.get("/th/tours/")
        assert resp.status_code == 200

    def test_only_published(self, client, tour, draft_tour):
        resp = client.get("/en/tours/")
        assert tour.title in resp.content.decode()
        assert draft_tour.title not in resp.content.decode()

    def test_search_filter(self, client, tour):
        resp = client.get("/en/tours/", {"q": "Tokyo"})
        assert tour.title in resp.content.decode()

    def test_search_no_match(self, client, tour):
        resp = client.get("/en/tours/", {"q": "nonexistent_xyz"})
        assert tour.title not in resp.content.decode()

    def test_destination_filter(self, client, tour, destination):
        resp = client.get("/en/tours/", {"destination": "japan"})
        assert tour.title in resp.content.decode()

    def test_category_filter(self, client, tour, category):
        resp = client.get("/en/tours/", {"category": "beach"})
        assert tour.title in resp.content.decode()

    def test_context_has_filters(self, client, tour):
        resp = client.get("/th/tours/")
        assert "current_filters" in resp.context
        assert "destinations" in resp.context
        assert "categories" in resp.context


@pytest.mark.django_db
class TestTourDetailView:
    def test_tour_detail_200(self, client, tour):
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert resp.status_code == 200

    def test_draft_tour_404(self, client, draft_tour):
        resp = client.get(f"/th/tours/{draft_tour.slug}/")
        assert resp.status_code == 404

    def test_context_has_inquiry_form(self, client, tour):
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert "inquiry_form" in resp.context

    def test_context_has_related_tours(self, client, tour):
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert "related_tours" in resp.context


@pytest.mark.django_db
class TestTourPdfView:
    def test_pdf_response(self, client, tour):
        resp = client.get(f"/th/tours/{tour.slug}/pdf/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_draft_tour_pdf_404(self, client, draft_tour):
        resp = client.get(f"/th/tours/{draft_tour.slug}/pdf/")
        assert resp.status_code == 404
