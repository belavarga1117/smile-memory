"""Security tests — CSRF, auth, production settings, headers."""

import pytest


@pytest.mark.django_db
class TestCSRFProtection:
    """POST endpoints must require CSRF tokens."""

    def test_inquiry_post_without_csrf_rejected(self, client):
        """POST to inquiry endpoint without CSRF should be rejected (403)."""
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        resp = csrf_client.post(
            "/th/bookings/inquire/nonexistent/",
            {"contact_name": "Test"},
        )
        assert resp.status_code == 403

    def test_contact_post_without_csrf_rejected(self, client):
        from django.test import Client

        csrf_client = Client(enforce_csrf_checks=True)
        resp = csrf_client.post(
            "/th/contact/",
            {"name": "Test", "email": "t@t.com", "message": "hi"},
        )
        assert resp.status_code == 403


class TestProductionSecuritySettings:
    """Verify production settings have correct security configuration."""

    def test_ssl_redirect_enabled(self):
        """Production must redirect HTTP → HTTPS."""
        from config.settings import production as prod

        assert prod.SECURE_SSL_REDIRECT is True

    def test_hsts_enabled(self):
        from config.settings import production as prod

        assert prod.SECURE_HSTS_SECONDS >= 31536000  # at least 1 year
        assert prod.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
        assert prod.SECURE_HSTS_PRELOAD is True

    def test_session_cookie_secure(self):
        from config.settings import production as prod

        assert prod.SESSION_COOKIE_SECURE is True

    def test_csrf_cookie_secure(self):
        from config.settings import production as prod

        assert prod.CSRF_COOKIE_SECURE is True

    def test_content_type_nosniff(self):
        from config.settings import production as prod

        assert prod.SECURE_CONTENT_TYPE_NOSNIFF is True

    def test_x_frame_options_deny(self):
        from config.settings import production as prod

        assert prod.X_FRAME_OPTIONS == "DENY"

    def test_debug_is_false(self):
        from config.settings import production as prod

        assert prod.DEBUG is False


@pytest.mark.django_db
class TestAuthProtection:
    """Test that admin/dashboard require authentication."""

    def test_admin_requires_login(self, client):
        resp = client.get("/admin/", follow=False)
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_dashboard_requires_staff(self, client):
        resp = client.get("/dashboard/", follow=False)
        assert resp.status_code == 302
        assert "login" in resp.url

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_api_is_public_read_only(self, client):
        """API endpoints should be publicly readable (AllowAny)."""
        resp = client.get("/api/v1/tours/")
        assert resp.status_code == 200

        resp = client.get("/api/v1/destinations/")
        assert resp.status_code == 200

        resp = client.get("/api/v1/categories/")
        assert resp.status_code == 200


class TestDjangoChecks:
    """Django system check framework tests."""

    def test_system_check_passes(self):
        """Django check should pass without critical errors."""
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        try:
            call_command("check", verbosity=0, stdout=out)
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"Django system check failed: {out.getvalue()}")
