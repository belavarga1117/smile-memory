from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.tours.models import Tour


class TourSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Tour.objects.filter(status=Tour.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return [
            "pages:home",
            "pages:about",
            "pages:contact",
            "pages:payment_info",
            "pages:privacy",
            "pages:terms",
            "tours:list",
            "blog:list",
        ]

    def location(self, item):
        return reverse(item)
