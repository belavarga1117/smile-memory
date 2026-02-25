"""Tests for spam protection: honeypot fields and rate limiting."""

import pytest
from django.test import RequestFactory


@pytest.mark.django_db
class TestHoneypotField:
    """Tests for HoneypotField and HoneypotFormMixin."""

    def test_honeypot_field_empty_valid(self):
        """Empty honeypot field passes validation."""
        from apps.pages.forms import ContactForm

        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Hello",
            "message": "A test message",
            "website_url": "",  # honeypot empty = OK
        }
        form = ContactForm(data=data)
        assert form.is_valid(), form.errors

    def test_honeypot_field_filled_invalid(self):
        """Filled honeypot field rejects form."""
        from apps.pages.forms import ContactForm

        data = {
            "name": "Bot User",
            "email": "bot@example.com",
            "subject": "Spam",
            "message": "Buy cheap products",
            "website_url": "http://spam.com",  # honeypot filled = bot
        }
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert "website_url" in form.errors

    def test_honeypot_widget_is_hidden(self):
        """Honeypot field renders with CSS to hide it from real users."""
        from apps.core.spam_protection import HoneypotField

        field = HoneypotField()
        widget_attrs = field.widget.attrs
        # Should have style or tabindex to hide from real users
        assert "style" in widget_attrs or "tabindex" in widget_attrs


@pytest.mark.django_db
class TestRateLimit:
    """Tests for session-based rate limiting."""

    def _make_request_with_session(self):
        """Create a request with a real session."""
        from django.contrib.sessions.backends.db import SessionStore

        factory = RequestFactory()
        request = factory.post("/contact/")
        request.session = SessionStore()
        return request

    def test_first_submission_allowed(self):
        """First submission within window is allowed."""
        from apps.core.spam_protection import check_rate_limit

        request = self._make_request_with_session()
        result = check_rate_limit(request, key="test", max_count=3, window=300)
        assert result is True

    def test_within_limit_allowed(self):
        """Submissions within limit are all allowed."""
        from apps.core.spam_protection import check_rate_limit

        request = self._make_request_with_session()
        for _ in range(3):
            result = check_rate_limit(request, key="test", max_count=3, window=300)
            assert result is True

    def test_exceeding_limit_blocked(self):
        """Submission exceeding the limit is blocked."""
        from apps.core.spam_protection import check_rate_limit

        request = self._make_request_with_session()
        for _ in range(3):
            check_rate_limit(request, key="test2", max_count=3, window=300)

        result = check_rate_limit(request, key="test2", max_count=3, window=300)
        assert result is False

    def test_rate_limit_response_status(self):
        """rate_limit_response() returns a 403 response."""
        from apps.core.spam_protection import rate_limit_response

        resp = rate_limit_response()
        assert resp.status_code == 403

    def test_expired_timestamps_removed(self):
        """Timestamps outside the window do not count toward the limit."""
        import time
        from apps.core.spam_protection import check_rate_limit

        request = self._make_request_with_session()
        # Inject old timestamps (outside window)
        old_time = time.time() - 400  # 400s ago > 300s window
        request.session["test_old"] = [old_time, old_time, old_time]

        # Should be allowed because old timestamps are expired
        result = check_rate_limit(request, key="test_old", max_count=3, window=300)
        assert result is True


@pytest.mark.django_db
class TestContactFormRateLimit:
    """Integration test: contact form respects rate limit."""

    def test_contact_form_rate_limited(self, client):
        """After 3 submissions, the 4th is rejected."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Hello",
            "message": "Test message",
            "website_url": "",
        }

        # First 3 should succeed (redirects to /contact/)
        for _ in range(3):
            resp = client.post("/en/contact/", data)
            # 200 = form error re-render, 302 = success redirect — both are NOT 403
            assert resp.status_code in (200, 302)

        # 4th should be blocked (rate limited)
        resp = client.post("/en/contact/", data)
        assert resp.status_code == 403


@pytest.mark.django_db
class TestInquiryFormHoneypot:
    """Tests honeypot on inquiry form."""

    def test_inquiry_honeypot_blocks_bots(self, client, tour, departure):
        """Inquiry form with filled honeypot returns 403 or form error."""
        data = {
            "contact_name": "Bot",
            "contact_email": "bot@example.com",
            "contact_phone": "+66812345678",
            "num_adults": 2,
            "num_children": 0,
            "departure": departure.pk,
            "website_url": "http://spam.com",  # honeypot filled
        }
        client.post(f"/en/tours/{tour.slug}/inquire/", data)
        # Should not create inquiry
        from apps.bookings.models import Inquiry

        assert Inquiry.objects.count() == 0
