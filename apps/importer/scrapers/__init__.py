"""Web scrapers for wholesaler tour data."""

from .go365 import Go365Scraper
from .gs25 import GS25Scraper
from .realjourney import RealJourneyScraper
from .zego import ZegoScraper

SCRAPERS = {
    "go365": Go365Scraper,
    "gs25": GS25Scraper,
    "realjourney": RealJourneyScraper,
    "zego": ZegoScraper,
}


def get_scraper(source: str, **kwargs):
    """Factory: return a scraper instance by source name."""
    cls = SCRAPERS.get(source.lower())
    if not cls:
        available = ", ".join(sorted(SCRAPERS.keys()))
        raise ValueError(f"Unknown scraper: {source!r}. Available: {available}")
    return cls(**kwargs)
