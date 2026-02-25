"""Base scraper interface for wholesaler tour websites."""

import logging
import random
import time
import urllib.request
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Realistic browser headers to avoid IP blocking
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


class BaseScraper:
    """Abstract base for wholesaler website scrapers.

    Provides polite HTTP fetching with:
    - Random delays between requests (2-5s)
    - Realistic browser headers
    - Session cookies
    - Retry with exponential backoff
    - Configurable rate limiting
    """

    source_name = ""  # e.g. "go365", "zego", "gs25"
    base_url = ""

    def __init__(self, min_delay=2.0, max_delay=5.0, max_retries=2):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self._request_count = 0
        self._last_request_time = 0

        # Cookie jar for session persistence
        self._cookie_jar = CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._cookie_jar)
        )

    def discover_tours(self, country=None) -> list[dict]:
        """Return list of {url, external_id, title} dicts.

        Override in subclasses.
        """
        raise NotImplementedError

    def scrape_tour(self, url: str) -> dict | None:
        """Scrape one tour detail page → dict of Tour-compatible fields.

        Returns None if page cannot be parsed.
        Override in subclasses.
        """
        raise NotImplementedError

    def scrape_all(self, country=None) -> list[dict]:
        """Discover + scrape all tours. Returns list of parsed tour dicts."""
        discovered = self.discover_tours(country=country)
        logger.info("Discovered %d tour URLs", len(discovered))

        results = []
        for i, tour_info in enumerate(discovered, 1):
            url = tour_info["url"]
            logger.info("[%d/%d] Scraping: %s", i, len(discovered), url)
            try:
                data = self.scrape_tour(url)
                if data:
                    results.append(data)
                    logger.info("  → OK: %s", data.get("title", "?")[:60])
                else:
                    logger.warning("  → No data parsed from %s", url)
            except Exception:
                logger.exception("  → Failed: %s", url)

        logger.info(
            "Scraping complete: %d/%d tours parsed successfully",
            len(results),
            len(discovered),
        )
        return results

    def _fetch(self, url: str, referer: str | None = None) -> BeautifulSoup:
        """HTTP GET → BeautifulSoup, with rate limiting and retry."""
        # Encode spaces and other unsafe chars in URL path
        url = self._safe_url(url)
        self._rate_limit()

        headers = dict(DEFAULT_HEADERS)
        if referer:
            headers["Referer"] = referer
        elif self.base_url:
            headers["Referer"] = self.base_url

        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(url, headers=headers)
                response = self._opener.open(req, timeout=30)
                html = response.read()

                # Try UTF-8 first, then fallback
                try:
                    html_str = html.decode("utf-8")
                except UnicodeDecodeError:
                    html_str = html.decode("tis-620", errors="replace")

                self._request_count += 1
                return BeautifulSoup(html_str, "lxml")

            except HTTPError as e:
                if e.code == 429:
                    # Rate limited — back off significantly
                    wait = (attempt + 1) * 10 + random.uniform(5, 15)
                    logger.warning("Rate limited (429) on %s, waiting %.1fs", url, wait)
                    time.sleep(wait)
                elif e.code in (500, 502, 503, 504):
                    wait = (attempt + 1) * 5 + random.uniform(2, 5)
                    logger.warning(
                        "Server error %d on %s, retry %d/%d in %.1fs",
                        e.code,
                        url,
                        attempt + 1,
                        self.max_retries,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error("HTTP %d on %s", e.code, url)
                    raise
            except URLError as e:
                wait = (attempt + 1) * 3 + random.uniform(1, 3)
                logger.warning(
                    "URL error on %s: %s, retry %d/%d",
                    url,
                    e.reason,
                    attempt + 1,
                    self.max_retries,
                )
                time.sleep(wait)

        raise ConnectionError(
            f"Failed to fetch {url} after {self.max_retries + 1} attempts"
        )

    def _fetch_raw(self, url: str) -> str:
        """HTTP GET → raw HTML string (no BeautifulSoup)."""
        self._rate_limit()

        headers = dict(DEFAULT_HEADERS)
        headers["Referer"] = self.base_url

        req = urllib.request.Request(url, headers=headers)
        response = self._opener.open(req, timeout=30)
        html = response.read()

        try:
            return html.decode("utf-8")
        except UnicodeDecodeError:
            return html.decode("tis-620", errors="replace")

    def _rate_limit(self):
        """Sleep a random amount between requests to be polite."""
        now = time.time()
        elapsed = now - self._last_request_time
        min_wait = self.min_delay + random.uniform(0, self.max_delay - self.min_delay)

        if elapsed < min_wait:
            sleep_time = min_wait - elapsed
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _abs_url(self, href: str) -> str:
        """Convert relative URL to absolute."""
        return urljoin(self.base_url, href)

    def _safe_url(self, url: str) -> str:
        """Encode spaces and unsafe characters in URL path."""
        parsed = urlparse(url)
        # Only encode the path component (spaces → %20)
        safe_path = quote(parsed.path, safe="/:@!$&'()*+,;=-._~")
        return urlunparse(parsed._replace(path=safe_path))
