"""Email notifications for booking inquiries."""

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send_async(subject, message, from_email, recipient_list, html_message):
    """Send email in background thread so it never blocks the request."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as exc:
        logger.error("Email send failed to %s: %s", recipient_list, exc)


def _dispatch(subject, message, recipient_list, html_message):
    # In tests (locmem backend) send synchronously so mail.outbox works
    if "locmem" in settings.EMAIL_BACKEND:
        _send_async(
            subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message
        )
        return
    t = threading.Thread(
        target=_send_async,
        args=(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            html_message,
        ),
        daemon=True,
    )
    t.start()


def send_inquiry_thank_you(inquiry):
    """Send thank-you email to customer after inquiry submission."""
    subject = f"Thank you for your inquiry — {inquiry.reference_number}"
    html_message = render_to_string(
        "emails/inquiry_thank_you.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME},
    )
    _dispatch(
        subject=subject,
        message=f"Thank you for your inquiry ({inquiry.reference_number}). "
        f"We will review your request and get back to you within 24 hours.",
        recipient_list=[inquiry.contact_email],
        html_message=html_message,
    )


def send_inquiry_notification_to_admin(inquiry):
    """Notify admin about new inquiry."""
    subject = f"New Inquiry: {inquiry.reference_number} — {inquiry.contact_name}"
    html_message = render_to_string(
        "emails/inquiry_admin_notification.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME},
    )
    _dispatch(
        subject=subject,
        message=f"New inquiry {inquiry.reference_number} from {inquiry.contact_name} "
        f"for {inquiry.tour.title if inquiry.tour else 'N/A'}. "
        f"Check admin panel for details.",
        recipient_list=[settings.ADMIN_EMAIL],
        html_message=html_message,
    )


def send_booking_confirmation(inquiry):
    """Send booking confirmation email after admin approves."""
    subject = f"Booking Confirmed — {inquiry.reference_number}"
    html_message = render_to_string(
        "emails/booking_confirmed.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME},
    )
    _dispatch(
        subject=subject,
        message=f"Your booking ({inquiry.reference_number}) has been confirmed! "
        f"Please check the details in the email.",
        recipient_list=[inquiry.contact_email],
        html_message=html_message,
    )


def send_booking_rejection(inquiry, reason=""):
    """Send rejection/unavailability email."""
    subject = f"Update on your inquiry — {inquiry.reference_number}"
    html_message = render_to_string(
        "emails/booking_rejected.html",
        {"inquiry": inquiry, "reason": reason, "site_name": settings.SITE_NAME},
    )
    _dispatch(
        subject=subject,
        message=f"We're sorry, but your inquiry ({inquiry.reference_number}) "
        f"could not be confirmed at this time.",
        recipient_list=[inquiry.contact_email],
        html_message=html_message,
    )
