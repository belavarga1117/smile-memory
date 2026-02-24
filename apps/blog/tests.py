"""Tests for blog app — models, views."""

import pytest
from django.urls import reverse

from apps.blog.models import BlogCategory, BlogPost, Tag


# ── Model Tests ──


class TestBlogCategoryModel:
    def test_str(self, blog_category):
        assert str(blog_category) == "Travel Tips"

    def test_auto_slug(self, db):
        bc = BlogCategory(name="Destination Guides")
        bc.save()
        assert bc.slug == "destination-guides"


class TestTagModel:
    def test_str(self, blog_tag):
        assert str(blog_tag) == "Japan"

    def test_auto_slug(self, db):
        t = Tag(name="South Korea")
        t.save()
        assert t.slug == "south-korea"


class TestBlogPostModel:
    def test_str(self, blog_post):
        assert str(blog_post) == "Top 10 Tokyo Tips"

    def test_get_absolute_url(self, blog_post):
        assert blog_post.get_absolute_url() == reverse(
            "blog:detail", kwargs={"slug": "top-10-tokyo-tips"}
        )

    def test_auto_slug(self, db, blog_category):
        post = BlogPost(
            title="My New Post",
            body="Content here",
            category=blog_category,
            status=BlogPost.Status.PUBLISHED,
        )
        post.save()
        assert post.slug == "my-new-post"

    def test_featured_img_url_fallback(self, blog_post):
        blog_post.featured_image_url = "https://example.com/img.jpg"
        assert blog_post.featured_img == "https://example.com/img.jpg"


# ── View Tests ──


@pytest.mark.django_db
class TestBlogListView:
    def test_list_200(self, client, blog_post):
        resp = client.get("/th/blog/")
        assert resp.status_code == 200

    def test_only_published(self, client, blog_post, db):
        draft = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            body="Draft content",
            status=BlogPost.Status.DRAFT,
        )
        resp = client.get("/th/blog/")
        content = resp.content.decode()
        assert blog_post.title in content
        assert draft.title not in content

    def test_category_filter(self, client, blog_post, blog_category):
        resp = client.get("/th/blog/", {"category": "travel-tips"})
        assert blog_post.title in resp.content.decode()

    def test_tag_filter(self, client, blog_post, blog_tag):
        resp = client.get("/th/blog/", {"tag": "japan"})
        assert blog_post.title in resp.content.decode()

    def test_search(self, client, blog_post):
        resp = client.get("/th/blog/", {"q": "Tokyo"})
        assert blog_post.title in resp.content.decode()

    def test_context(self, client, blog_post):
        resp = client.get("/th/blog/")
        assert "categories" in resp.context
        assert "current_filters" in resp.context


@pytest.mark.django_db
class TestBlogDetailView:
    def test_detail_200(self, client, blog_post):
        resp = client.get(f"/th/blog/{blog_post.slug}/")
        assert resp.status_code == 200

    def test_context_has_related_posts(self, client, blog_post):
        resp = client.get(f"/th/blog/{blog_post.slug}/")
        assert "related_posts" in resp.context

    def test_draft_post_404(self, client, db):
        draft = BlogPost.objects.create(
            title="Draft", slug="draft-hidden", body="X", status=BlogPost.Status.DRAFT
        )
        resp = client.get(f"/th/blog/{draft.slug}/")
        assert resp.status_code == 404
