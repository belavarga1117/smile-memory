"""Real Journey (realjourney.co.th) tour API client.

Uses the TourProX WordPress AJAX API (no authentication required).
Single API call returns all tours with full pricing, departures, and media URLs.

Data flow:
1. GET /wp-admin/admin-ajax.php?action=get_tours_ajax → all tours with departures
   (pagesize=500 to get everything in one request)

Previous version used HTML scraping; this API approach is faster and more reliable.
"""

import json
import logging
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .base import BaseScraper

logger = logging.getLogger(__name__)


class RealJourneyScraper(BaseScraper):
    """API client for Real Journey via TourProX AJAX endpoint."""

    source_name = "realjourney"
    base_url = "https://realjourney.co.th"

    AJAX_URL = (
        "https://realjourney.co.th/wp-admin/admin-ajax.php"
        "?action=get_tours_ajax&mode=searchresultsproduct"
        "&pagesize=500&pagenumber=1&sortby=price"
    )

    def __init__(self, **kwargs):
        super().__init__(min_delay=1.0, max_delay=2.0, max_retries=2)

    # ------------------------------------------------------------------ #
    #  Tour discovery (one API call for everything)
    # ------------------------------------------------------------------ #

    def discover_tours(self, country=None) -> list[dict]:
        """Fetch all tours from the AJAX API.

        Returns one entry per product with _raw_product attached.
        """
        self._rate_limit()

        url = self.AJAX_URL
        if country:
            url += f"&country={country.lower()}"

        raw = self._fetch_json(url)
        products = raw.get("res_data", {}).get("products", [])

        results = []
        for product in products:
            product_slug = product.get("product_slug", "")
            title = product.get("product_name", "")

            results.append(
                {
                    "url": f"{self.base_url}/tour/{product_slug}/",
                    "external_id": str(product.get("product_id", "")),
                    "title": title,
                    "_raw_product": product,
                }
            )

        logger.info(
            "Discovered %d tours from Real Journey API",
            len(results),
        )
        return results

    def _fetch_json(self, url: str) -> dict:
        """HTTP GET → parsed JSON."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.base_url,
        }
        req = urllib.request.Request(url, headers=headers)
        response = self._opener.open(req, timeout=60)
        return json.loads(response.read().decode("utf-8"))

    # ------------------------------------------------------------------ #
    #  Tour parsing (from raw API data)
    # ------------------------------------------------------------------ #

    def scrape_tour(self, url: str) -> dict | None:
        """Not used for API-based flow. See scrape_program()."""
        logger.warning("scrape_tour() called directly — use discover_tours() flow")
        return None

    def scrape_program(self, tour_info: dict) -> dict | None:
        """Parse a tour from pre-fetched API data.

        Args:
            tour_info: dict from discover_tours() with _raw_product
        """
        product = tour_info.get("_raw_product")
        if not product:
            return None

        # Basic info
        title = product.get("product_name", "")
        product_code = product.get("product_code", "")
        product_slug = product.get("product_slug", "")

        # Strip product code prefix from title (API returns "RJ-XJ107 ทัวร์..." format)
        formatted_code = self._format_product_code(product_code)
        title = self._strip_product_code(title, formatted_code)

        # Duration
        days = self._to_int(product.get("stay_day"))
        nights = self._to_int(product.get("stay_night"))

        # Price
        price_from = self._to_decimal(product.get("price_product"))

        # Country / destination
        country_name = product.get("country_name", "")
        # Map Thai country names to English
        dest_name = self._thai_country_to_english(country_name)

        # Airline
        airline_code = product.get("airlinecode", "")

        # Hotel stars
        hotel_stars = self._to_int(product.get("star_hotel"))

        # Highlight
        highlight = product.get("highlight", "")

        # Hero image
        hero_image_url = product.get("url_pic", "")

        # PDF / Word URLs
        pdf_url = product.get("url_pdf", "")
        word_url = product.get("url_word", "")

        # Source URL
        source_url = f"{self.base_url}/tour/{product_slug}/"

        # Parse departures from periods
        departures = []
        for period in product.get("periods", []):
            dep = self._parse_period(period)
            if dep:
                departures.append(dep)

        # Build images list
        images = []
        if hero_image_url:
            images.append(hero_image_url)
        banner_url = product.get("url_banner", "")
        if banner_url and banner_url != hero_image_url:
            images.append(banner_url)

        data = {
            "title": title,
            "title_th": title,
            "product_code": self._format_product_code(product_code),
            "duration_days": days,
            "duration_nights": nights,
            "price_from": price_from,
            "destination_name": dest_name,
            "airline_code": airline_code,
            "highlight": highlight,
            "highlight_th": highlight,
            "hotel_stars_min": hotel_stars,
            "hotel_stars_max": hotel_stars,
            "source": "realjourney",
            "source_url": source_url,
            "external_id": str(product.get("product_id", "")),
            "hero_image_url": hero_image_url,
            "pdf_url": pdf_url,
            "word_url": word_url,
            # Related data
            "_departures": departures,
            "_images": images,
            "_itinerary": [],  # Not in API (only in downloadable PDF)
            "_flights": [],
        }

        return data

    # ------------------------------------------------------------------ #
    #  Period / departure parsing
    # ------------------------------------------------------------------ #

    def _parse_period(self, period: dict) -> dict | None:
        """Parse one period from the API response."""
        dep_date = self._parse_iso_date(period.get("period_start_value"))
        ret_date = self._parse_iso_date(period.get("period_end_value"))

        if not dep_date:
            return None

        price_adult = self._to_decimal(period.get("price_adults_double"))
        if not price_adult:
            price_adult = self._to_decimal(period.get("price"))

        # Status
        soldout = period.get("period_soldout", "false")
        status_code = period.get("periodstatuscode", "")
        if soldout == "true" or status_code == "PRSoldout":
            status = "soldout"
        elif status_code == "PRClose":
            status = "closed"
        else:
            status = "available"

        # Single supplement (difference between single and double)
        price_single = self._to_decimal(period.get("price_adults_single"))
        price_single_supplement = None
        if price_single and price_adult and price_single > price_adult:
            price_single_supplement = price_single - price_adult

        dep = {
            "departure_date": dep_date,
            "return_date": ret_date or dep_date,
            "price_adult": price_adult,
            "status": status,
            "period_code": str(period.get("period_id", "")),
            # Extra pricing
            "price_child": self._to_decimal(period.get("price_child_withbed")),
            "price_child_no_bed": self._to_decimal(period.get("price_child_nobed")),
            "price_single_supplement": price_single_supplement,
            "price_join_land": self._to_decimal(period.get("price_joinland")),
            # Capacity
            "group_size": self._to_int(period.get("groupsize")),
            "booked": (
                self._to_int(period.get("groupsize", 0))
                - self._to_int(period.get("seatremain", 0))
            )
            if period.get("groupsize") and period.get("seatremain")
            else None,
        }

        # Promo pricing
        price_before = self._to_decimal(period.get("price_before_discount"))
        discount = self._to_int(period.get("discount_display"))
        if discount and discount > 0 and price_before and price_adult:
            if price_adult < price_before:
                dep["price_adult_promo"] = price_adult

        return dep

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _parse_iso_date(self, date_str):
        """Parse ISO date like '2026-04-01T00:00:00' → date."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "")).date()
        except (ValueError, TypeError):
            return None

    def _to_decimal(self, val) -> Decimal | None:
        """Convert to Decimal, returning None for zero/empty."""
        if val is None or val == "" or val == 0 or val == "0":
            return None
        try:
            d = Decimal(str(val).replace(",", "").strip())
            return d if d > 0 else None
        except (InvalidOperation, ValueError):
            return None

    def _to_int(self, val) -> int | None:
        """Convert to int."""
        if val is None or val == "":
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _format_product_code(self, code: str) -> str:
        """Format product code: RJHUCKG01 → RJ-HUCKG01."""
        if not code:
            return ""
        code = code.upper().replace("-", "")
        if code.startswith("RJ") and len(code) > 2:
            return f"RJ-{code[2:]}"
        return code

    def _strip_product_code(self, title: str, product_code: str) -> str:
        """Strip product code prefix from title.

        The RealJourney API embeds the product code at the start of product_name,
        e.g. "RJ-XJ107 ทัวร์ เรียล เรียล..." → "ทัวร์ เรียล เรียล..."
        """
        if not title:
            return title
        if product_code and title.startswith(product_code + " "):
            return title[len(product_code) :].lstrip()
        return title

    def _thai_country_to_english(self, thai_name: str) -> str:
        """Map Thai country names to English."""
        mapping = {
            "ญี่ปุ่น": "Japan",
            "จีน": "China",
            "เวียดนาม": "Vietnam",
            "เกาหลี": "South Korea",
            "ฮ่องกง": "Hong Kong",
            "ไต้หวัน": "Taiwan",
            "สิงคโปร์": "Singapore",
            "มาเลเซีย": "Malaysia",
            "อินเดีย": "India",
            "ตุรกี": "Turkey",
            "อียิปต์": "Egypt",
            "จอร์แดน": "Jordan",
            "คาซัคสถาน": "Kazakhstan",
            "ยุโรป": "Europe",
            "อิตาลี": "Italy",
            "ฝรั่งเศส": "France",
            "สวิตเซอร์แลนด์": "Switzerland",
            "เยอรมนี": "Germany",
        }
        for thai, eng in mapping.items():
            if thai in thai_name:
                return eng
        # Return as-is if no mapping found
        return thai_name
