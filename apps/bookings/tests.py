"""Tests for bookings app — models, views, forms, workflow."""

from unittest.mock import patch

import pytest

from apps.bookings.forms import InquiryForm
from apps.bookings.models import Inquiry, InquiryNote
from apps.customers.models import Customer


# ── Model Tests ──


class TestInquiryModel:
    def test_str(self, inquiry):
        assert inquiry.reference_number in str(inquiry)
        assert "John Doe" in str(inquiry)

    def test_auto_reference_number(self, inquiry):
        assert inquiry.reference_number.startswith("SM-")
        parts = inquiry.reference_number.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 3  # 3-digit sequence

    def test_reference_uniqueness(self, inquiry, customer, tour):
        inq2 = Inquiry.objects.create(
            customer=customer,
            tour=tour,
            contact_name="Jane Doe",
            contact_email="jane@test.com",
        )
        assert inq2.reference_number != inquiry.reference_number

    def test_reference_sequence(self, inquiry, customer, tour):
        inq2 = Inquiry.objects.create(
            customer=customer,
            tour=tour,
            contact_name="Jane Doe",
            contact_email="jane@test.com",
        )
        seq1 = int(inquiry.reference_number.split("-")[-1])
        seq2 = int(inq2.reference_number.split("-")[-1])
        assert seq2 == seq1 + 1

    def test_total_travelers(self, inquiry):
        assert inquiry.total_travelers == 3  # 2 adults + 1 child + 0 infant

    def test_status_choices(self):
        assert Inquiry.Status.NEW == "new"
        assert Inquiry.Status.CONFIRMED == "confirmed"
        assert Inquiry.Status.REJECTED == "rejected"
        assert Inquiry.Status.CANCELLED == "cancelled"

    def test_default_status(self, inquiry):
        assert inquiry.status == Inquiry.Status.NEW


class TestInquiryNoteModel:
    def test_str(self, inquiry, admin_user):
        note = InquiryNote.objects.create(
            inquiry=inquiry, author=admin_user, note="Contacted customer"
        )
        assert inquiry.reference_number in str(note)


# ── Form Tests ──


class TestInquiryForm:
    def test_valid_form(self):
        data = {
            "contact_name": "Test User",
            "contact_email": "test@example.com",
            "contact_phone": "+66812345678",
            "num_adults": 2,
            "num_children": 0,
            "num_infants": 0,
            "room_preference": "double",
            "special_requests": "",
            "marketing_opt_in": True,
        }
        form = InquiryForm(data=data)
        assert form.is_valid()

    def test_minimal_valid_form(self):
        data = {
            "contact_name": "Test User",
            "contact_email": "test@example.com",
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
        }
        form = InquiryForm(data=data)
        assert form.is_valid()

    def test_invalid_email(self):
        data = {
            "contact_name": "Test",
            "contact_email": "not-an-email",
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
        }
        form = InquiryForm(data=data)
        assert not form.is_valid()
        assert "contact_email" in form.errors

    def test_missing_name(self):
        data = {
            "contact_email": "test@example.com",
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
        }
        form = InquiryForm(data=data)
        assert not form.is_valid()
        assert "contact_name" in form.errors


# ── View Tests ──


@pytest.mark.django_db
class TestInquiryCreateView:
    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_valid_inquiry_submission(self, mock_admin, mock_thank, client, tour):
        data = {
            "contact_name": "New Customer",
            "contact_email": "newcust@test.com",
            "contact_phone": "+66999999999",
            "num_adults": 2,
            "num_children": 0,
            "num_infants": 0,
            "room_preference": "twin",
            "special_requests": "Vegetarian meals",
            "marketing_opt_in": True,
        }
        resp = client.post(f"/th/bookings/inquire/{tour.slug}/", data)
        assert resp.status_code == 302  # Redirect after success

        # Verify inquiry created
        inq = Inquiry.objects.filter(contact_email="newcust@test.com").first()
        assert inq is not None
        assert inq.tour == tour
        assert inq.num_adults == 2
        assert inq.status == Inquiry.Status.NEW

        # Verify customer created
        cust = Customer.objects.get(email="newcust@test.com")
        assert cust.first_name == "New"
        assert cust.last_name == "Customer"
        assert cust.marketing_opt_in is True

    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_inquiry_increments_customer_count(
        self, mock_admin, mock_thank, client, tour, customer
    ):
        old_count = customer.total_inquiries
        data = {
            "contact_name": "John Doe",
            "contact_email": customer.email,
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
        }
        client.post(f"/th/bookings/inquire/{tour.slug}/", data)
        customer.refresh_from_db()
        assert customer.total_inquiries == old_count + 1

    def test_invalid_form_rerenders(self, client, tour):
        data = {"contact_name": "", "contact_email": "bad"}
        resp = client.post(f"/th/bookings/inquire/{tour.slug}/", data)
        assert resp.status_code == 200  # Re-renders the page

    def test_draft_tour_404(self, client, draft_tour):
        resp = client.post(f"/th/bookings/inquire/{draft_tour.slug}/", {})
        assert resp.status_code == 404


@pytest.mark.django_db
class TestInquirySuccessView:
    def test_success_page(self, client, inquiry):
        resp = client.get(f"/th/bookings/success/{inquiry.reference_number}/")
        assert resp.status_code == 200

    def test_invalid_reference_404(self, client):
        resp = client.get("/th/bookings/success/SM-00000000-999/")
        assert resp.status_code == 404
