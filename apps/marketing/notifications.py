"""Email notifications for marketing: newsletter welcome, campaign sends."""

import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send_async(subject, message, from_email, recipient_list, html_message):
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


def send_newsletter_welcome(subscriber):
    """Send welcome email to new subscriber — in their signup language."""
    lang = getattr(subscriber, "language", "th") or "th"
    site_url = "https://smilememorytravel.com"
    unsubscribe_url = f"{site_url}/{'th' if lang == 'th' else 'en'}/newsletter/unsubscribe/{subscriber.unsubscribe_token}/"

    subject = (
        "ยินดีต้อนรับสู่ Smile Memory! 🌏"
        if lang == "th"
        else "Welcome to Smile Memory Newsletter! ✈️"
    )
    html_message = render_to_string(
        f"emails/newsletter_welcome_{lang}.html",
        {
            "subscriber": subscriber,
            "site_name": settings.SITE_NAME,
            "unsubscribe_url": unsubscribe_url,
        },
    )
    plain = (
        f"ยินดีต้อนรับ! ขอบคุณที่สมัครรับข่าวสาร Smile Memory\nยกเลิก: {unsubscribe_url}"
        if lang == "th"
        else f"Welcome! Thank you for subscribing to Smile Memory newsletter.\nUnsubscribe: {unsubscribe_url}"
    )
    _dispatch(subject, plain, [subscriber.email], html_message)


def send_newsletter_confirmation(subscriber):
    """Send double opt-in confirmation email to new subscriber."""
    lang = getattr(subscriber, "language", "th") or "th"
    site_url = "https://smilememorytravel.com"
    confirm_url = (
        f"{site_url}/{'th' if lang == 'th' else 'en'}"
        f"/newsletter/confirm/{subscriber.confirmation_token}/"
    )

    subject = (
        "ยืนยันการสมัครรับข่าวสาร Smile Memory 🌏"
        if lang == "th"
        else "Please confirm your Smile Memory subscription ✈️"
    )
    html_message = render_to_string(
        f"emails/newsletter_confirm_{lang}.html",
        {
            "subscriber": subscriber,
            "site_name": settings.SITE_NAME,
            "confirm_url": confirm_url,
        },
    )
    plain = (
        f"กรุณายืนยันการสมัครรับข่าวสาร Smile Memory:\n{confirm_url}"
        if lang == "th"
        else f"Please confirm your Smile Memory newsletter subscription:\n{confirm_url}"
    )
    _dispatch(subject, plain, [subscriber.email], html_message)
