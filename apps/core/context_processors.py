import logging

from django.conf import settings

logger = logging.getLogger(__name__)


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
