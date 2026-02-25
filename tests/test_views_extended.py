"""Extended view tests: tour list/detail, homepage, pages, bilingual URLs."""

import pytest


@pytest.mark.django_db
class TestTourListView:
    """Tests for tour list page."""

    def test_list_returns_200(self, client, tour):
        resp = client.get("/en/tours/")
        assert resp.status_code == 200

    def test_list_shows_published_tours(self, client, tour):
        resp = client.get("/en/tours/")
        assert tour.title in resp.content.decode()

    def test_list_hides_draft_tours(self, client, draft_tour):
        resp = client.get("/en/tours/")
        assert draft_tour.title not in resp.content.decode()

    def test_list_filter_by_destination(self, client, tour, destination):
        resp = client.get("/en/tours/", {"destination": destination.slug})
        assert resp.status_code == 200
        assert tour.title in resp.content.decode()

    def test_list_filter_by_category(self, client, tour, category):
        resp = client.get("/en/tours/", {"category": category.slug})
        assert resp.status_code == 200

    def test_list_search(self, client, tour):
        resp = client.get("/en/tours/", {"q": "Tokyo"})
        assert resp.status_code == 200

    def test_list_thai_url(self, client, tour):
        resp = client.get("/th/tours/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestTourDetailView:
    """Tests for tour detail page."""

    def test_detail_returns_200(self, client, tour):
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200

    def test_detail_shows_tour_title(self, client, tour):
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert tour.title in resp.content.decode()

    def test_detail_404_for_draft(self, client, draft_tour):
        resp = client.get(f"/en/tours/{draft_tour.slug}/")
        assert resp.status_code == 404

    def test_detail_shows_itinerary(self, client, tour, itinerary_day):
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200
        assert itinerary_day.title in resp.content.decode()

    def test_detail_shows_inquiry_form(self, client, tour, departure):
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200
        assert "inquiry_form" in resp.context

    def test_detail_pdf_url(self, client, tour):
        tour.pdf_url = "https://example.com/tour.pdf"
        tour.save()
        resp = client.get(f"/en/tours/{tour.slug}/")
        assert resp.status_code == 200

    def test_detail_thai_url(self, client, tour):
        resp = client.get(f"/th/tours/{tour.slug}/")
        assert resp.status_code == 200


@pytest.mark.django_db
class TestHomepageView:
    """Tests for homepage."""

    def test_homepage_200(self, client, hero_slide):
        resp = client.get("/en/")
        assert resp.status_code == 200

    def test_homepage_has_featured_tours(self, client, tour, hero_slide):
        tour.is_featured = True
        tour.save()
        resp = client.get("/en/")
        assert resp.status_code == 200
        assert "featured_tours" in resp.context

    def test_homepage_has_testimonials(self, client, testimonial):
        resp = client.get("/en/")
        assert "testimonials" in resp.context

    def test_homepage_has_faqs(self, client, faq):
        resp = client.get("/en/")
        assert "faqs" in resp.context

    def test_homepage_thai(self, client):
        resp = client.get("/th/")
        assert resp.status_code == 200

    def test_root_redirects_to_language(self, client):
        resp = client.get("/")
        assert resp.status_code in (301, 302)


@pytest.mark.django_db
class TestStaticPages:
    """Tests for about, contact, payment info pages."""

    def test_about_200(self, client):
        assert client.get("/en/about/").status_code == 200

    def test_contact_200(self, client):
        assert client.get("/en/contact/").status_code == 200

    def test_payment_info_200(self, client):
        assert client.get("/en/payment-info/").status_code == 200

    def test_contact_has_faq(self, client, faq):
        resp = client.get("/en/contact/")
        assert "faqs" in resp.context

    def test_pages_in_thai(self, client):
        for path in ["/th/about/", "/th/contact/", "/th/payment-info/"]:
            resp = client.get(path)
            assert resp.status_code == 200, f"{path} returned {resp.status_code}"


@pytest.mark.django_db
class TestDashboardView:
    """Tests for admin dashboard."""

    def test_dashboard_requires_staff(self, client):
        resp = client.get("/dashboard/")
        assert resp.status_code in (302, 403)

    def test_dashboard_accessible_by_staff(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_dashboard_has_kpi_context(self, client, staff_user):
        client.force_login(staff_user)
        resp = client.get("/dashboard/")
        assert "total_tours" in resp.context
        assert "new_inquiries" in resp.context


@pytest.mark.django_db
class TestMarketingViews:
    """Tests for newsletter subscribe/unsubscribe."""

    def test_subscribe_valid_email(self, client):
        resp = client.post(
            "/en/newsletter/subscribe/",
            {"email": "newuser@example.com", "website_url": ""},
        )
        assert resp.status_code in (200, 302)
        from apps.marketing.models import Subscriber

        assert Subscriber.objects.filter(email="newuser@example.com").exists()

    def test_subscribe_duplicate_email_no_error(self, client):
        """Subscribing twice with same email doesn't crash."""
        data = {"email": "dup@example.com", "website_url": ""}
        client.post("/en/newsletter/subscribe/", data)
        resp = client.post("/en/newsletter/subscribe/", data)
        assert resp.status_code in (200, 302)

    def test_unsubscribe_valid_token(self, client):
        from apps.marketing.models import Subscriber
        import uuid

        sub = Subscriber.objects.create(
            email="unsub@example.com",
            is_active=True,
            unsubscribe_token=uuid.uuid4(),
        )
        resp = client.get(f"/en/newsletter/unsubscribe/{sub.unsubscribe_token}/")
        assert resp.status_code == 200

    def test_unsubscribe_invalid_token_404(self, client):
        import uuid

        resp = client.get(f"/en/newsletter/unsubscribe/{uuid.uuid4()}/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestBlogViews:
    """Tests for blog list and detail views."""

    def test_blog_list_200(self, client):
        resp = client.get("/en/blog/")
        assert resp.status_code == 200

    def test_blog_list_shows_published(self, client, blog_post):
        resp = client.get("/en/blog/")
        assert blog_post.title in resp.content.decode()

    def test_blog_detail_200(self, client, blog_post):
        resp = client.get(f"/en/blog/{blog_post.slug}/")
        assert resp.status_code == 200

    def test_blog_detail_draft_404(self, client, blog_category):
        from apps.blog.models import BlogPost

        draft = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            status=BlogPost.Status.DRAFT,
            category=blog_category,
        )
        resp = client.get(f"/en/blog/{draft.slug}/")
        assert resp.status_code == 404

    def test_blog_category_filter(self, client, blog_post, blog_category):
        resp = client.get("/en/blog/", {"category": blog_category.slug})
        assert resp.status_code == 200

    def test_blog_list_thai(self, client):
        resp = client.get("/th/blog/")
        assert resp.status_code == 200
