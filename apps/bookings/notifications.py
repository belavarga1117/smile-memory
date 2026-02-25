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


def _lang(inquiry):
    """Return 'th' or 'en' from inquiry, defaulting to 'th'."""
    return getattr(inquiry, "language", "th") or "th"


def send_inquiry_thank_you(inquiry):
    """Send thank-you email — language matches customer's browsing language."""
    lang = _lang(inquiry)
    subject = (
        f"ขอบคุณที่สอบถาม — {inquiry.reference_number}"
        if lang == "th"
        else f"Thank you for your inquiry — {inquiry.reference_number}"
    )
    html_message = render_to_string(
        f"emails/inquiry_thank_you_{lang}.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME},
    )
    plain = (
        f"ขอบคุณ ({inquiry.reference_number}). เราจะติดต่อกลับภายใน 24 ชั่วโมง"
        if lang == "th"
        else f"Thank you for your inquiry ({inquiry.reference_number}). We will get back to you within 24 hours."
    )
    _dispatch(subject, plain, [inquiry.contact_email], html_message)


def send_inquiry_notification_to_admin(inquiry):
    """Notify admin — always in Thai (admin is Thai-speaking)."""
    subject = f"[Inquiry ใหม่] {inquiry.reference_number} — {inquiry.contact_name}"
    admin_url = (
        f"{settings.SITE_URL}/admin/bookings/inquiry/{inquiry.pk}/change/"
        if hasattr(settings, "SITE_URL")
        else f"https://web-production-86e1f.up.railway.app/admin/bookings/inquiry/{inquiry.pk}/change/"
    )
    html_message = render_to_string(
        "emails/inquiry_admin_notification.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME, "admin_url": admin_url},
    )
    plain = (
        f"Inquiry ใหม่ {inquiry.reference_number} จาก {inquiry.contact_name} "
        f"({inquiry.contact_email}) สำหรับ {inquiry.tour.title if inquiry.tour else 'N/A'}."
    )
    _dispatch(subject, plain, [settings.ADMIN_EMAIL], html_message)


def send_booking_confirmation(inquiry):
    """Send booking confirmation — language matches inquiry language."""
    lang = _lang(inquiry)
    subject = (
        f"ยืนยันการจองแล้ว — {inquiry.reference_number}"
        if lang == "th"
        else f"Booking Confirmed — {inquiry.reference_number}"
    )
    html_message = render_to_string(
        f"emails/booking_confirmed_{lang}.html",
        {"inquiry": inquiry, "site_name": settings.SITE_NAME},
    )
    plain = (
        f"การจองของท่านได้รับการยืนยันแล้ว ({inquiry.reference_number})."
        if lang == "th"
        else f"Your booking ({inquiry.reference_number}) has been confirmed!"
    )
    _dispatch(subject, plain, [inquiry.contact_email], html_message)


def send_booking_rejection(inquiry, reason=""):
    """Send rejection email — language matches inquiry language."""
    lang = _lang(inquiry)
    subject = (
        f"อัปเดตการสอบถาม — {inquiry.reference_number}"
        if lang == "th"
        else f"Update on your inquiry — {inquiry.reference_number}"
    )
    html_message = render_to_string(
        f"emails/booking_rejected_{lang}.html",
        {"inquiry": inquiry, "reason": reason, "site_name": settings.SITE_NAME},
    )
    plain = (
        f"ขออภัย ไม่สามารถยืนยันการจองได้ ({inquiry.reference_number})."
        if lang == "th"
        else f"We could not confirm your booking ({inquiry.reference_number})."
    )
    _dispatch(subject, plain, [inquiry.contact_email], html_message)
