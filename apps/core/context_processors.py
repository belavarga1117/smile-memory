from django.conf import settings


def site_config(request):
    """Make site configuration available in all templates."""
    from .models import SiteConfiguration

    try:
        config = SiteConfiguration.get()
    except Exception:
        config = None

    return {
        "site_config": config,
        "SITE_NAME": settings.SITE_NAME,
    }
