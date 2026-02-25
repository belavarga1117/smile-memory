"""Brevo transactional email backend using REST API (bypasses SMTP port blocking)."""

import logging

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class BrevoEmailBackend(BaseEmailBackend):
    """Send emails via Brevo REST API instead of SMTP.

    Required setting:
        BREVO_API_KEY — API key from Brevo dashboard (SMTP & API → API Keys)

    Falls back gracefully: logs error, never raises, so email failures
    never crash views.
    """

    API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_key = getattr(settings, "BREVO_API_KEY", "")

    def send_messages(self, email_messages):
        if not self.api_key:
            logger.error("BrevoEmailBackend: BREVO_API_KEY not set — emails not sent")
            return 0

        sent = 0
        for message in email_messages:
            try:
                sent += self._send_one(message)
            except Exception as exc:
                logger.error("Brevo API error sending to %s: %s", message.to, exc)
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, message):
        import json
        import urllib.request

        # Resolve html body from alternatives
        html_content = None
        if hasattr(message, "alternatives"):
            for content, mime in message.alternatives:
                if mime == "text/html":
                    html_content = content
                    break

        from_email, from_name = self._parse_address(
            message.from_email or settings.DEFAULT_FROM_EMAIL
        )

        payload = {
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": addr} for addr in message.to],
            "subject": message.subject,
            "textContent": message.body,
        }
        if html_content:
            payload["htmlContent"] = html_content

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(  # noqa: S310
            self.API_URL,
            data=data,
            headers={
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            status = resp.status
            if status == 201:
                return 1
            body = resp.read().decode("utf-8", errors="replace")
            logger.error("Brevo API returned %s: %s", status, body)
            return 0

    @staticmethod
    def _parse_address(address):
        """Parse 'Name <email>' or plain 'email'."""
        if "<" in address and address.endswith(">"):
            name, rest = address.split("<", 1)
            return rest.rstrip(">").strip(), name.strip()
        return address.strip(), "Smile Memory"
