import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def language_urls(request):
    """Compute alternate-language URLs for hreflang SEO tags.

    All i18n_patterns URLs start with /th/ or /en/.
    Produces th_url and en_url for the current page.
    """
    path = request.path_info
    if path.startswith("/th/"):
        th_url = path
        en_url = "/en/" + path[4:]
    elif path.startswith("/en/"):
        th_url = "/th/" + path[4:]
        en_url = path
    else:
        th_url = "/th/"
        en_url = "/en/"
    return {"th_url": th_url, "en_url": en_url}


def site_config(request):
    """Make site configuration available in all templates."""
    from .models import SiteConfiguration

    try:
        config = SiteConfiguration.get()
    except Exception:
        logger.error("Failed to load SiteConfiguration", exc_info=True)
        config = None

    return {
        "site_config": config,
        "SITE_NAME": settings.SITE_NAME,
    }
