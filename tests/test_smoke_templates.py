"""Template/UI smoke tests — verify pages render without errors.

Tests all major pages in both /en and /th languages,
checks for key HTML elements and bilingual content.
"""

import pytest

from .factories import (
    BlogPostFactory,
    DestinationFactory,
    FAQFactory,
    HeroSlideFactory,
    TourDepartureFactory,
    TourFactory,
    TourImageFactory,
    TrustBadgeFactory,
    ItineraryDayFactory,
)


@pytest.mark.django_db
class TestHomepageSmoke:
    def test_homepage_en(self, client):
        HeroSlideFactory()
        TrustBadgeFactory()
        FAQFactory()
        resp = client.get("/en/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Smile Memory" in content or "smile" in content.lower()

    def test_homepage_th(self, client):
        HeroSlideFactory()
        resp = client.get("/th/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestTourListSmoke:
    def test_tour_list_en(self, client):
        dest = DestinationFactory()
        TourFactory(destinations=[dest])
        resp = client.get("/en/tours/")
        assert resp.status_code == 200
        assert b"tours" in resp.content.lower() or b"tour" in resp.content.lower()

    def test_tour_list_th(self, client):
        TourFactory()
        resp = client.get("/th/tours/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestTourDetailSmoke:
    def test_tour_detail_en(self, client):
        tour = TourFactory(title="Tokyo Explorer EN", title_th="สำรวจโตเกียว")
        TourDepartureFactory(tour=tour)
        ItineraryDayFactory(tour=tour, day_number=1)
        TourImageFactory(tour=tour)

        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Should show English title
        assert "Tokyo Explorer EN" in content

    def test_tour_detail_th(self, client):
        tour = TourFactory(title="Tokyo Explorer", title_th="สำรวจโตเกียว")
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert resp.status_code == 200
        content = resp.content.decode()
        # Should show Thai title (via trans_field)
        assert "สำรวจโตเกียว" in content

    def test_tour_detail_has_inquiry_form(self, client):
        tour = TourFactory()
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "contact_name" in content or "inquiry" in content.lower()


@pytest.mark.django_db
class TestContactSmoke:
    def test_contact_page_en(self, client):
        resp = client.get("/en/contact/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "contact" in content.lower() or "form" in content.lower()

    def test_contact_page_th(self, client):
        resp = client.get("/th/contact/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestAboutSmoke:
    def test_about_page_en(self, client):
        resp = client.get("/en/about/")
        assert resp.status_code == 200

    def test_about_page_th(self, client):
        resp = client.get("/th/about/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestBlogSmoke:
    def test_blog_list_en(self, client):
        BlogPostFactory()
        resp = client.get("/en/blog/")
        assert resp.status_code == 200

    def test_blog_list_th(self, client):
        BlogPostFactory()
        resp = client.get("/th/blog/")
        assert resp.status_code == 200

    def test_blog_detail_en(self, client):
        post = BlogPostFactory(title="Test Blog Post", title_th="บทความทดสอบ")
        resp = client.get(f"/en/blog/{post.slug}/")
        assert resp.status_code == 200
        assert "Test Blog Post" in resp.content.decode()


@pytest.mark.django_db
class TestPaymentInfoSmoke:
    def test_payment_info_en(self, client):
        resp = client.get("/en/payment-info/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestBilingualRendering:
    """Verify trans_field returns the correct language version."""

    def test_tour_list_shows_thai_title_on_th_url(self, client):
        TourFactory(title="English Title", title_th="ชื่อไทย")
        resp = client.get("/th/tours/")
        content = resp.content.decode()
        assert "ชื่อไทย" in content

    def test_tour_list_shows_english_title_on_en_url(self, client):
        TourFactory(title="English Title", title_th="ชื่อไทย")
        resp = client.get("/en/tours/")
        content = resp.content.decode()
        assert "English Title" in content
