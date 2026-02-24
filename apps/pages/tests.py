"""Tests for pages app — models, views, forms."""

import pytest

from apps.pages.forms import ContactForm
from apps.pages.models import ContactMessage


# ── Model Tests ──


class TestHeroSlideModel:
    def test_str(self, hero_slide):
        assert str(hero_slide) == "Discover Japan"

    def test_bg_image_url_fallback(self, hero_slide):
        hero_slide.image_url = "https://example.com/hero.jpg"
        assert hero_slide.bg_image == "https://example.com/hero.jpg"


class TestTestimonialModel:
    def test_str(self, testimonial):
        assert "Somchai" in str(testimonial)
        assert "5" in str(testimonial)


class TestTrustBadgeModel:
    def test_str(self, trust_badge):
        assert "10,000+" in str(trust_badge)


class TestFAQModel:
    def test_str(self, faq):
        assert "How do I book?" in str(faq)


class TestContactMessageModel:
    def test_str(self, db):
        msg = ContactMessage.objects.create(
            name="Test User",
            email="test@test.com",
            subject="Question",
            message="Hello",
        )
        assert "Test User" in str(msg)
        assert "Question" in str(msg)

    def test_default_is_read(self, db):
        msg = ContactMessage.objects.create(
            name="Test", email="t@t.com", subject="S", message="M"
        )
        assert msg.is_read is False


# ── Form Tests ──


class TestContactForm:
    def test_valid_form(self):
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+66812345678",
            "subject": "General Inquiry",
            "message": "I want to know more about your tours.",
        }
        form = ContactForm(data=data)
        assert form.is_valid()

    def test_missing_required_fields(self):
        form = ContactForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "email" in form.errors
        assert "subject" in form.errors
        assert "message" in form.errors

    def test_invalid_email(self):
        data = {
            "name": "Test",
            "email": "not-email",
            "subject": "Test",
            "message": "Hello",
        }
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_phone_optional(self):
        data = {
            "name": "Test",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Hello",
        }
        form = ContactForm(data=data)
        assert form.is_valid()


# ── View Tests ──


@pytest.mark.django_db
class TestHomePageView:
    def test_home_200(self, client):
        resp = client.get("/th/")
        assert resp.status_code == 200

    def test_home_context(
        self, client, hero_slide, testimonial, trust_badge, faq, tour
    ):
        resp = client.get("/th/")
        assert "hero_slides" in resp.context
        assert "featured_tours" in resp.context
        assert "testimonials" in resp.context
        assert "trust_badges" in resp.context
        assert "faqs" in resp.context


@pytest.mark.django_db
class TestAboutView:
    def test_about_200(self, client):
        resp = client.get("/th/about/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestContactView:
    def test_contact_get_200(self, client):
        resp = client.get("/th/contact/")
        assert resp.status_code == 200

    def test_contact_post_valid(self, client):
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "",
            "subject": "Question",
            "message": "Hello, I want to book a tour.",
        }
        resp = client.post("/th/contact/", data)
        assert resp.status_code == 302  # Redirect on success
        assert ContactMessage.objects.count() == 1

    def test_contact_post_invalid(self, client):
        resp = client.post("/th/contact/", {})
        assert resp.status_code == 200  # Re-renders with errors


@pytest.mark.django_db
class TestPaymentInfoView:
    def test_payment_info_200(self, client):
        resp = client.get("/th/payment-info/")
        assert resp.status_code == 200
