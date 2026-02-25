"""Tests for Brevo email backend and core context processor."""

import json
from unittest.mock import MagicMock, patch

import pytest
from django.core.mail import EmailMultiAlternatives
from django.test import RequestFactory, override_settings


@pytest.mark.django_db
class TestBrevoEmailBackend:
    """Tests for BrevoEmailBackend — HTTP REST API email sending."""

    def _get_backend(self):
        from apps.core.email_backends import BrevoEmailBackend

        with override_settings(BREVO_API_KEY="test-brevo-key"):
            return BrevoEmailBackend()

    def _make_message(self, subject="Hello", body="Text body", to=None, html=None):
        msg = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email="Smile Memory <noreply@smilememorytravel.com>",
            to=to or ["test@example.com"],
        )
        if html:
            msg.attach_alternative(html, "text/html")
        return msg

    def test_no_api_key_returns_0(self):
        """Without API key, send_messages returns 0 and logs error."""
        from apps.core.email_backends import BrevoEmailBackend

        with override_settings(BREVO_API_KEY=""):
            backend = BrevoEmailBackend()
        result = backend.send_messages([self._make_message()])
        assert result == 0

    def test_send_plain_text_message(self):
        """Sending a plain text email calls Brevo API and returns 1."""
        backend = self._get_backend()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 201

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            result = backend.send_messages([self._make_message()])

        assert result == 1
        assert mock_open.called
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["subject"] == "Hello"
        assert payload["textContent"] == "Text body"
        assert payload["to"] == [{"email": "test@example.com"}]

    def test_send_html_message(self):
        """HTML alternative is included in Brevo payload."""
        backend = self._get_backend()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 201

        msg = self._make_message(html="<h1>Hello</h1>")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = backend.send_messages([msg])

        assert result == 1

    def test_api_error_returns_0(self):
        """Non-201 response returns 0."""
        backend = self._get_backend()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 400
        mock_resp.read.return_value = b'{"message":"Bad Request"}'

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = backend.send_messages([self._make_message()])

        assert result == 0

    def test_send_multiple_messages(self):
        """Multiple messages: returns count of successfully sent."""
        backend = self._get_backend()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 201

        msgs = [self._make_message(subject=f"Msg {i}") for i in range(3)]
        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = backend.send_messages(msgs)

        assert result == 3

    def test_network_exception_fail_silently(self):
        """Network error with fail_silently=True returns 0 without raising."""
        backend = self._get_backend()
        backend.fail_silently = True

        with patch(
            "urllib.request.urlopen", side_effect=Exception("Connection refused")
        ):
            result = backend.send_messages([self._make_message()])

        assert result == 0

    def test_network_exception_raises_when_not_silent(self):
        """Network error with fail_silently=False raises."""
        backend = self._get_backend()
        backend.fail_silently = False

        with patch("urllib.request.urlopen", side_effect=Exception("timeout")):
            with pytest.raises(Exception, match="timeout"):
                backend.send_messages([self._make_message()])

    def test_parse_address_with_name(self):
        from apps.core.email_backends import BrevoEmailBackend

        email, name = BrevoEmailBackend._parse_address("Smile Memory <info@smile.com>")
        assert email == "info@smile.com"
        assert name == "Smile Memory"

    def test_parse_address_plain_email(self):
        from apps.core.email_backends import BrevoEmailBackend

        email, name = BrevoEmailBackend._parse_address("info@smile.com")
        assert email == "info@smile.com"
        assert name == "Smile Memory"

    def test_sender_name_in_payload(self):
        """Sender name is extracted from from_email."""
        backend = self._get_backend()
        mock_resp = MagicMock()
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 201

        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            backend.send_messages([self._make_message()])

        req = mock_open.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["sender"]["name"] == "Smile Memory"
        assert payload["sender"]["email"] == "noreply@smilememorytravel.com"


@pytest.mark.django_db
class TestSiteConfigContextProcessor:
    """Tests for site_config context processor."""

    def test_context_processor_adds_site_config(self, client):
        """site_config is available in all template contexts."""
        resp = client.get("/en/")
        assert "site_config" in resp.context

    def test_context_processor_adds_site_name(self, client):
        """SITE_NAME constant is in context."""
        resp = client.get("/en/")
        assert "SITE_NAME" in resp.context

    def test_context_processor_handles_db_error(self):
        """If SiteConfiguration fails, context returns None (no crash)."""
        from apps.core.context_processors import site_config

        factory = RequestFactory()
        request = factory.get("/")

        with patch(
            "apps.core.models.SiteConfiguration.get",
            side_effect=Exception("DB down"),
        ):
            ctx = site_config(request)

        assert ctx["site_config"] is None
