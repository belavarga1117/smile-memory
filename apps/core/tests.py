"""Tests for core app — models, template tags, dashboard."""

import pytest
from django.template import Context, Template
from django.test import RequestFactory

from apps.core.models import SiteConfiguration


# ── Model Tests ──


class TestSiteConfiguration:
    def test_singleton(self, db):
        sc1 = SiteConfiguration.get()
        sc2 = SiteConfiguration.get()
        assert sc1.pk == sc2.pk == 1

    def test_str(self, db):
        sc = SiteConfiguration.get()
        assert str(sc) == "Smile Memory"

    def test_save_enforces_pk1(self, db):
        sc = SiteConfiguration(site_name="Test", pk=99)
        sc.save()
        assert sc.pk == 1


# ── Template Tag Tests ──


@pytest.mark.django_db
class TestTransFieldTag:
    def test_english_field(self, tour):
        from django.utils.translation import activate

        activate("en")
        tpl = Template('{% load i18n_fields %}{% trans_field tour "title" %}')
        ctx = Context({"tour": tour})
        result = tpl.render(ctx).strip()
        assert result == "Tokyo Explorer"

    def test_thai_field(self, tour):
        from django.utils.translation import activate

        activate("th")
        tpl = Template('{% load i18n_fields %}{% trans_field tour "title" %}')
        ctx = Context({"tour": tour})
        result = tpl.render(ctx).strip()
        assert result == "สำรวจโตเกียว"
        activate("en")

    def test_fallback_when_th_empty(self):
        from django.utils.translation import activate

        from apps.tours.models import Tour

        activate("th")
        t = Tour.objects.create(title="English Only", slug="english-only")
        tpl = Template('{% load i18n_fields %}{% trans_field tour "title" %}')
        ctx = Context({"tour": t})
        result = tpl.render(ctx).strip()
        assert result == "English Only"
        activate("en")


@pytest.mark.django_db
class TestTfFilter:
    def test_filter_english(self, tour):
        tpl = Template('{% load i18n_fields %}{{ tour|tf:"title" }}')
        ctx = Context({"tour": tour})
        result = tpl.render(ctx).strip()
        assert result == "Tokyo Explorer"

    def test_filter_thai(self, tour, settings):
        from django.utils.translation import activate

        activate("th")
        tpl = Template('{% load i18n_fields %}{{ tour|tf:"title" }}')
        ctx = Context({"tour": tour})
        result = tpl.render(ctx).strip()
        assert result == "สำรวจโตเกียว"
        activate("en")


@pytest.mark.django_db
class TestSwitchLanguageUrlTag:
    def test_switch_to_thai(self):
        factory = RequestFactory()
        request = factory.get("/en/tours/")
        tpl = Template('{% load i18n_fields %}{% switch_language_url "th" %}')
        ctx = Context({"request": request})
        result = tpl.render(ctx).strip()
        assert result == "/th/tours/"

    def test_switch_to_english(self):
        factory = RequestFactory()
        request = factory.get("/th/tours/tokyo-explorer/")
        tpl = Template('{% load i18n_fields %}{% switch_language_url "en" %}')
        ctx = Context({"request": request})
        result = tpl.render(ctx).strip()
        assert result == "/en/tours/tokyo-explorer/"

    def test_no_request(self):
        tpl = Template('{% load i18n_fields %}{% switch_language_url "en" %}')
        ctx = Context({})
        result = tpl.render(ctx).strip()
        assert result == "/en/"


# ── Dashboard View Tests ──


@pytest.mark.django_db
class TestDashboardView:
    def test_dashboard_requires_staff(self, client):
        resp = client.get("/dashboard/")
        assert resp.status_code == 302  # Redirects to login

    def test_dashboard_staff_access(self, client, staff_user):
        client.login(username="staff", password="testpass123")
        resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_dashboard_has_context(self, client, staff_user, tour, inquiry):
        client.login(username="staff", password="testpass123")
        resp = client.get("/dashboard/")
        assert "total_tours" in resp.context
        assert "total_inquiries" in resp.context
        assert "total_customers" in resp.context
