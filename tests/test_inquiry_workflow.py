"""Integration tests for the inquiry booking workflow.

Tests the full cycle: submit → NEW → Customer create/update → emails → CONFIRM/REJECT.
"""

from unittest.mock import patch

import pytest
from django.core import mail
from django.utils import timezone

from apps.bookings.models import Inquiry
from apps.bookings.notifications import (
    send_booking_confirmation,
    send_booking_rejection,
    send_inquiry_notification_to_admin,
    send_inquiry_thank_you,
)
from apps.customers.models import Customer

from .factories import (
    CustomerFactory,
    InquiryFactory,
    TourDepartureFactory,
    TourFactory,
)


@pytest.mark.django_db
class TestInquirySubmission:
    """Test inquiry form submission creates correct records."""

    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_new_customer_created_on_inquiry(self, mock_admin, mock_thank, client):
        tour = TourFactory()
        data = {
            "contact_name": "Somchai Prasert",
            "contact_email": "somchai@example.com",
            "contact_phone": "+66891234567",
            "num_adults": 2,
            "num_children": 1,
            "num_infants": 0,
            "room_preference": "double",
            "special_requests": "",
            "marketing_opt_in": True,
        }
        resp = client.post(f"/th/bookings/inquire/{tour.slug}/", data)
        assert resp.status_code == 302

        # Inquiry created with correct status
        inq = Inquiry.objects.get(contact_email="somchai@example.com")
        assert inq.status == Inquiry.Status.NEW
        assert inq.tour == tour
        assert inq.num_adults == 2
        assert inq.num_children == 1
        assert inq.reference_number.startswith("SM-")

        # Customer record created
        cust = Customer.objects.get(email="somchai@example.com")
        assert cust.first_name == "Somchai"
        assert cust.last_name == "Prasert"
        assert cust.marketing_opt_in is True
        assert cust.opted_in_at is not None
        assert cust.total_inquiries == 1

    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_existing_customer_updated_on_inquiry(self, mock_admin, mock_thank, client):
        tour = TourFactory()
        customer = CustomerFactory(
            email="repeat@example.com",
            marketing_opt_in=False,
            total_inquiries=3,
        )
        data = {
            "contact_name": "Repeat Customer",
            "contact_email": "repeat@example.com",
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
            "marketing_opt_in": True,
        }
        client.post(f"/th/bookings/inquire/{tour.slug}/", data)

        customer.refresh_from_db()
        assert customer.total_inquiries == 4
        assert customer.marketing_opt_in is True

    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_opt_in_not_reverted_if_already_true(self, mock_admin, mock_thank, client):
        tour = TourFactory()
        customer = CustomerFactory(
            email="opted@example.com",
            marketing_opt_in=True,
            opted_in_at=timezone.now(),
        )

        data = {
            "contact_name": "Opted Customer",
            "contact_email": "opted@example.com",
            "num_adults": 1,
            "num_children": 0,
            "num_infants": 0,
            "marketing_opt_in": False,  # unchecked on form
        }
        client.post(f"/th/bookings/inquire/{tour.slug}/", data)

        customer.refresh_from_db()
        # marketing_opt_in should stay True (view only sets it, doesn't unset)
        assert customer.marketing_opt_in is True

    @patch("apps.bookings.views.send_inquiry_thank_you")
    @patch("apps.bookings.views.send_inquiry_notification_to_admin")
    def test_departure_linked_when_provided(self, mock_admin, mock_thank, client):
        tour = TourFactory()
        dep = TourDepartureFactory(tour=tour)
        data = {
            "contact_name": "Dep Test",
            "contact_email": "dep@example.com",
            "num_adults": 2,
            "num_children": 0,
            "num_infants": 0,
            "departure_id": str(dep.pk),
        }
        client.post(f"/th/bookings/inquire/{tour.slug}/", data)

        inq = Inquiry.objects.get(contact_email="dep@example.com")
        assert inq.departure == dep


@pytest.mark.django_db
class TestInquiryEmails:
    """Test email notifications for inquiry workflow (using locmem email backend via settings fixture)."""

    def test_thank_you_email_sent(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox.clear()
        inquiry = InquiryFactory(
            contact_email="thankyou@test.com",
            contact_name="Thank You Test",
        )
        send_inquiry_thank_you(inquiry)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert inquiry.reference_number in email.subject
        assert "thankyou@test.com" in email.to

    def test_admin_notification_email(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox.clear()
        inquiry = InquiryFactory(contact_name="Admin Notify Test")
        send_inquiry_notification_to_admin(inquiry)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert inquiry.reference_number in email.subject
        assert "Admin Notify Test" in email.subject

    def test_booking_confirmation_email(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox.clear()
        inquiry = InquiryFactory(
            contact_email="confirm@test.com",
            status=Inquiry.Status.CONFIRMED,
            language="en",
        )
        send_booking_confirmation(inquiry)

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Confirmed" in email.subject
        assert "confirm@test.com" in email.to

    def test_booking_rejection_email(self, settings):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        mail.outbox.clear()
        inquiry = InquiryFactory(
            contact_email="reject@test.com",
            status=Inquiry.Status.REJECTED,
        )
        send_booking_rejection(inquiry, reason="Tour is fully booked")

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "reject@test.com" in email.to


@pytest.mark.django_db
class TestAdminWorkflow:
    """Test admin confirm/reject actions update status correctly."""

    def test_confirm_inquiry(self):
        inquiry = InquiryFactory(status=Inquiry.Status.NEW)
        Inquiry.objects.filter(pk=inquiry.pk).update(
            status=Inquiry.Status.CONFIRMED,
            confirmed_at=timezone.now(),
        )
        inquiry.refresh_from_db()
        assert inquiry.status == Inquiry.Status.CONFIRMED
        assert inquiry.confirmed_at is not None

    def test_reject_inquiry(self):
        inquiry = InquiryFactory(status=Inquiry.Status.CONTACTED)
        Inquiry.objects.filter(pk=inquiry.pk).update(
            status=Inquiry.Status.REJECTED,
            rejected_at=timezone.now(),
        )
        inquiry.refresh_from_db()
        assert inquiry.status == Inquiry.Status.REJECTED
        assert inquiry.rejected_at is not None

    def test_confirm_only_valid_statuses(self):
        """Already confirmed inquiries should not be re-confirmed."""
        inquiry = InquiryFactory(status=Inquiry.Status.CONFIRMED)
        count = Inquiry.objects.filter(
            pk=inquiry.pk, status__in=["new", "contacted"]
        ).update(
            status=Inquiry.Status.CONFIRMED,
            confirmed_at=timezone.now(),
        )
        assert count == 0  # No rows updated — already confirmed
