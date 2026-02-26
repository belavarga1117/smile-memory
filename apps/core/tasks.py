"""Shared Celery tasks for core functionality."""

import logging

from celery import shared_task
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(
    name="core.send_email",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # retry after 60s
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_email_task(self, subject, message, recipient_list, html_message, from_email):
    """Send a transactional email via Django email backend (Brevo in production).

    Retries up to 3 times with exponential backoff on failure.
    Called from bookings.notifications and marketing.notifications.
    """
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
        logger.error(
            "Email send failed to %s (subject: %s): %s",
            recipient_list,
            subject,
            exc,
            exc_info=True,
        )
        raise  # re-raise so Celery retry logic kicks in
