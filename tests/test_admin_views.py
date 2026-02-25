"""Tests for Django admin views — tour, customer, importer admin pages."""

import pytest

from .factories import (
    AirlineFactory,
    CategoryFactory,
    CustomerFactory,
    DestinationFactory,
    InquiryFactory,
    ItineraryDayFactory,
    TourDepartureFactory,
    TourFactory,
)


@pytest.mark.django_db
class TestTourAdmin:
    """Tests for TourAdmin list/detail/inline rendering."""

    def test_tour_admin_list_accessible(self, admin_client):
        TourFactory()
        resp = admin_client.get("/admin/tours/tour/")
        assert resp.status_code == 200

    def test_tour_admin_detail_accessible(self, admin_client):
        tour = TourFactory()
        resp = admin_client.get(f"/admin/tours/tour/{tour.pk}/change/")
        assert resp.status_code == 200

    def test_tour_admin_with_inlines(self, admin_client):
        """Tour detail page renders correctly with departure + itinerary inlines."""
        tour = TourFactory(with_departure=False)
        TourDepartureFactory(tour=tour)
        ItineraryDayFactory(tour=tour, day_number=1)
        resp = admin_client.get(f"/admin/tours/tour/{tour.pk}/change/")
        assert resp.status_code == 200

    def test_tour_admin_search(self, admin_client):
        TourFactory(title="Searchable Tour")
        resp = admin_client.get("/admin/tours/tour/?q=Searchable")
        assert resp.status_code == 200
        assert b"Searchable" in resp.content

    def test_destination_admin_list(self, admin_client):
        DestinationFactory()
        resp = admin_client.get("/admin/tours/destination/")
        assert resp.status_code == 200

    def test_category_admin_list(self, admin_client):
        CategoryFactory()
        resp = admin_client.get("/admin/tours/category/")
        assert resp.status_code == 200

    def test_airline_admin_list(self, admin_client):
        AirlineFactory()
        resp = admin_client.get("/admin/tours/airline/")
        assert resp.status_code == 200

    def test_tour_departure_admin_list(self, admin_client):
        TourDepartureFactory()
        resp = admin_client.get("/admin/tours/tourdeparture/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestBookingAdmin:
    """Tests for Inquiry admin."""

    def test_inquiry_admin_list_accessible(self, admin_client):
        InquiryFactory()
        resp = admin_client.get("/admin/bookings/inquiry/")
        assert resp.status_code == 200

    def test_inquiry_admin_detail_accessible(self, admin_client):
        inquiry = InquiryFactory()
        resp = admin_client.get(f"/admin/bookings/inquiry/{inquiry.pk}/change/")
        assert resp.status_code == 200

    def test_inquiry_admin_filter_by_status(self, admin_client):
        from apps.bookings.models import Inquiry

        InquiryFactory(status=Inquiry.Status.NEW)
        resp = admin_client.get("/admin/bookings/inquiry/?status=new")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestCustomerAdmin:
    """Tests for CustomerAdmin."""

    def test_customer_admin_list_accessible(self, admin_client):
        CustomerFactory()
        resp = admin_client.get("/admin/customers/customer/")
        assert resp.status_code == 200

    def test_customer_admin_filter_opted_in(self, admin_client):
        CustomerFactory(marketing_opt_in=True)
        CustomerFactory(marketing_opt_in=False)
        resp = admin_client.get("/admin/customers/customer/?marketing_opt_in__exact=1")
        assert resp.status_code == 200

    def test_customer_admin_requires_staff(self, client):
        resp = client.get("/admin/customers/customer/")
        assert resp.status_code in (302, 403)  # redirect to login


@pytest.mark.django_db
class TestMarketingAdmin:
    """Tests for Campaign and EmailTemplate admin."""

    def test_campaign_admin_list_accessible(self, admin_client):
        from tests.factories import CampaignFactory

        CampaignFactory()
        resp = admin_client.get("/admin/marketing/campaign/")
        assert resp.status_code == 200

    def test_email_template_admin_list_accessible(self, admin_client):
        from tests.factories import EmailTemplateFactory

        EmailTemplateFactory()
        resp = admin_client.get("/admin/marketing/emailtemplate/")
        assert resp.status_code == 200
