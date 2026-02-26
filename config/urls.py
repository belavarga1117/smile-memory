"""Root URL configuration for Smile Memory."""

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView
from rest_framework.routers import DefaultRouter

from apps.tours.viewsets import CategoryViewSet, DestinationViewSet, TourViewSet

from .sitemaps import BlogSitemap, StaticViewSitemap, TourSitemap

router = DefaultRouter()
router.register(r"tours", TourViewSet, basename="tour")
router.register(r"destinations", DestinationViewSet, basename="destination")
router.register(r"categories", CategoryViewSet, basename="category")

sitemaps = {
    "tours": TourSitemap,
    "blog": BlogSitemap,
    "static": StaticViewSitemap,
}

# Language-independent URLs (admin, API, SEO, language switcher)
urlpatterns = [
    # Root → redirect to Thai (default language)
    path("", RedirectView.as_view(url="/th/", permanent=False)),
    path("admin/", admin.site.urls),
    path("dashboard/", include("apps.core.urls")),
    path("api/v1/", include(router.urls)),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots_txt",
    ),
]

# Language-prefixed URLs (/th/..., /en/...)
urlpatterns += i18n_patterns(
    path("", include("apps.pages.urls")),
    path("tours/", include("apps.tours.urls")),
    path("blog/", include("apps.blog.urls")),
    path("bookings/", include("apps.bookings.urls")),
    path("newsletter/", include("apps.marketing.urls")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
