"""Tests for SEO (sitemap, robots.txt) and bilingual (i18n) functionality."""

import pytest


@pytest.mark.django_db
class TestSitemap:
    """Tests for sitemap.xml endpoint."""

    def test_sitemap_returns_200(self, client, tour):
        resp = client.get("/sitemap.xml")
        assert resp.status_code == 200

    def test_sitemap_content_type_xml(self, client, tour):
        resp = client.get("/sitemap.xml")
        assert "xml" in resp["Content-Type"]

    def test_sitemap_includes_tour_url(self, client, tour):
        resp = client.get("/sitemap.xml")
        assert tour.slug in resp.content.decode()

    def test_sitemap_includes_static_pages(self, client):
        resp = client.get("/sitemap.xml")
        content = resp.content.decode()
        assert "about" in content or "contact" in content

    def test_robots_txt_returns_200(self, client):
        resp = client.get("/robots.txt")
        assert resp.status_code == 200

    def test_robots_txt_allows_sitemap(self, client):
        resp = client.get("/robots.txt")
        content = resp.content.decode()
        assert "Sitemap" in content or "sitemap" in content

    def test_robots_txt_disallows_admin(self, client):
        resp = client.get("/robots.txt")
        content = resp.content.decode()
        assert "/admin" in content


@pytest.mark.django_db
class TestTransFieldTag:
    """Tests for {% trans_field %} template tag."""

    def test_trans_field_returns_english_by_default(self):
        from apps.core.templatetags.i18n_fields import trans_field
        from unittest.mock import patch

        class FakeObj:
            title = "English Title"
            title_th = "Thai Title"

        with patch(
            "apps.core.templatetags.i18n_fields.get_language", return_value="en"
        ):
            result = trans_field(FakeObj(), "title")
        assert result == "English Title"

    def test_trans_field_returns_thai_when_active(self):
        from apps.core.templatetags.i18n_fields import trans_field
        from unittest.mock import patch

        class FakeObj:
            title = "English Title"
            title_th = "Thai Title"

        with patch(
            "apps.core.templatetags.i18n_fields.get_language", return_value="th"
        ):
            result = trans_field(FakeObj(), "title")
        assert result == "Thai Title"

    def test_trans_field_falls_back_to_english_when_no_thai(self):
        from apps.core.templatetags.i18n_fields import trans_field
        from unittest.mock import patch

        class FakeObj:
            title = "English Title"
            title_th = ""  # empty Thai

        with patch(
            "apps.core.templatetags.i18n_fields.get_language", return_value="th"
        ):
            result = trans_field(FakeObj(), "title")
        assert result == "English Title"

    def test_trans_field_filter_works_same_as_tag(self):
        from apps.core.templatetags.i18n_fields import trans_field_filter
        from unittest.mock import patch

        class FakeObj:
            title = "EN"
            title_th = "TH"

        with patch(
            "apps.core.templatetags.i18n_fields.get_language", return_value="th"
        ):
            result = trans_field_filter(FakeObj(), "title")
        assert result == "TH"

    def test_switch_language_url_replaces_prefix(self):
        from apps.core.templatetags.i18n_fields import switch_language_url
        from django.test import RequestFactory

        rf = RequestFactory()
        request = rf.get("/en/tours/japan-tour/")
        ctx = {"request": request}
        result = switch_language_url(ctx, "th")
        assert result == "/th/tours/japan-tour/"

    def test_switch_language_url_no_request_returns_fallback(self):
        from apps.core.templatetags.i18n_fields import switch_language_url

        result = switch_language_url({}, "en")
        assert result == "/en/"


@pytest.mark.django_db
class TestBilingualViews:
    """Tests for bilingual URL routing and content switching."""

    def test_tour_detail_thai_shows_thai_title(self, client, tour):
        """Thai URL serves Thai content."""
        tour.title_th = "ทัวร์โตเกียว"
        tour.save()
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert resp.status_code == 200
        assert "ทัวร์โตเกียว" in resp.content.decode()

    def test_tour_list_thai_url(self, client, tour):
        resp = client.get("/th/tours/")
        assert resp.status_code == 200

    def test_blog_list_thai_url(self, client):
        resp = client.get("/th/blog/")
        assert resp.status_code == 200

    def test_root_redirects_to_language(self, client):
        resp = client.get("/")
        assert resp.status_code in (301, 302)

    def test_english_and_thai_urls_both_work(self, client, tour):
        for lang in ("en", "th"):
            resp = client.get(f"/{lang}/tours/{tour.slug}/")
            assert resp.status_code == 200, f"/{lang}/ returned {resp.status_code}"

    def test_language_switcher_url_tag(self):
        """switch_language_url tag correctly builds cross-language URLs."""
        from apps.core.templatetags.i18n_fields import switch_language_url
        from django.test import RequestFactory

        rf = RequestFactory()
        for from_lang, to_lang, path in [
            ("en", "th", "/en/tours/"),
            ("th", "en", "/th/blog/latest-post/"),
        ]:
            request = rf.get(f"/{from_lang}{path[3:]}")
            result = switch_language_url({"request": request}, to_lang)
            assert result.startswith(f"/{to_lang}/")


@pytest.mark.django_db
class TestBlogBilingual:
    """Tests for blog bilingual content (body_th, excerpt_th)."""

    def test_blog_detail_thai_shows_thai_body(self, client, blog_post):
        """Thai blog detail page uses body_th if set."""
        blog_post.body_th = "เนื้อหาไทย"
        blog_post.save()
        resp = client.get(f"/th/blog/{blog_post.slug}/")
        assert resp.status_code == 200
        assert "เนื้อหาไทย" in resp.content.decode()

    def test_blog_detail_english_shows_english_body(self, client, blog_post):
        resp = client.get(f"/en/blog/{blog_post.slug}/")
        assert resp.status_code == 200
        assert blog_post.body in resp.content.decode()

    def test_blog_list_shows_published_in_thai(self, client, blog_post):
        resp = client.get("/th/blog/")
        assert resp.status_code == 200
        assert blog_post.title in resp.content.decode()
