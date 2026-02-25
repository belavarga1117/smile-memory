"""Go365 Travel (go365travel.com) tour API client.

Uses the internal AJAX endpoints with CryptoJS AES decryption.
No authentication required — encryption key derived from current date.

Data flow:
1. GET /search/coverk → decrypt with date key → get passphrase
2. POST /search/LoadTour → decrypt → all tours (one row per departure)
3. Group by TourID → unique programs with departures

Optional per-tour call (only if more departure details needed):
4. POST /search/LoadPeriodListDate → decrypt → full departure pricing
"""

import base64
import hashlib
import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation

from .base import BaseScraper

logger = logging.getLogger(__name__)


def _evp_bytes_to_key(password: bytes, salt: bytes, key_len=32, iv_len=16):
    """OpenSSL EVP_BytesToKey (MD5-based) key derivation for CryptoJS compat."""
    d = b""
    d_i = b""
    while len(d) < key_len + iv_len:
        d_i = hashlib.md5(d_i + password + salt).digest()
        d += d_i
    return d[:key_len], d[key_len : key_len + iv_len]


def _decrypt_cryptojs(data: dict, passphrase: str) -> str:
    """Decrypt CryptoJS AES-CBC encrypted JSON payload."""
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad

    ct = base64.b64decode(data["ct"])
    iv = bytes.fromhex(data["iv"])
    salt = bytes.fromhex(data["s"])

    key, _ = _evp_bytes_to_key(passphrase.encode("utf-8"), salt)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ct), AES.block_size)
    return decrypted.decode("utf-8")


class Go365Scraper(BaseScraper):
    """API client for Go365 Travel internal AJAX endpoints.

    All tour data is retrieved via encrypted AJAX calls.
    The encryption is CryptoJS AES-CBC with a date-based passphrase.
    """

    source_name = "go365"
    base_url = "https://www.go365travel.com"

    def __init__(self, **kwargs):
        super().__init__(min_delay=1.0, max_delay=2.0, max_retries=2)
        self._passphrase = ""

    # ------------------------------------------------------------------ #
    #  Encryption key setup
    # ------------------------------------------------------------------ #

    def _ensure_passphrase(self):
        """Fetch and decrypt the daily passphrase from /search/coverk."""
        if self._passphrase:
            return

        self._rate_limit()
        date_key = datetime.now().strftime("%d%m%Y")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        }

        req = urllib.request.Request(f"{self.base_url}/search/coverk", headers=headers)
        resp = self._opener.open(req, timeout=30)
        coverk_data = json.loads(resp.read().decode("utf-8"))

        raw = _decrypt_cryptojs(coverk_data, date_key)
        self._passphrase = raw.strip('"')
        logger.info("Go365 passphrase obtained for %s", date_key)

    def _fetch_encrypted(self, path: str, post_data: dict | None = None) -> str:
        """Fetch an encrypted AJAX endpoint and return decrypted JSON string."""
        self._ensure_passphrase()
        self._rate_limit()

        url = f"{self.base_url}{path}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": self.base_url,
        }

        body = None
        if post_data:
            body = urllib.parse.urlencode(post_data).encode()

        req = urllib.request.Request(url, data=body, headers=headers)
        resp = self._opener.open(req, timeout=60)
        encrypted = json.loads(resp.read().decode("utf-8"))

        return _decrypt_cryptojs(encrypted, self._passphrase)

    # ------------------------------------------------------------------ #
    #  Tour discovery
    # ------------------------------------------------------------------ #

    def discover_tours(self, country=None) -> list[dict]:
        """Fetch all tours from the encrypted LoadTour endpoint.

        Returns one entry per unique TourID with _raw_rows containing
        all departure rows for that tour.
        """
        tours_json = self._fetch_encrypted("/search/LoadTour", {"page": "1"})
        all_rows = json.loads(tours_json)

        # Group by TourID (multiple rows = multiple departures of same tour)
        programs = {}
        for row in all_rows:
            tour_id = row.get("TourID", "")
            if not tour_id:
                continue

            # Filter by country
            if country:
                row_country = row.get("CountryEn", "")
                if country.lower() != row_country.lower():
                    continue

            if tour_id not in programs:
                wholesale_id = row.get("wholesale_id", "")
                programs[tour_id] = {
                    "url": (
                        f"{self.base_url}/tour/"
                        f"{row.get('CountryEn', 'Tour')}/"
                        f"{row.get('tour_id', '')}-{tour_id}-{wholesale_id}"
                    ),
                    "external_id": str(tour_id),
                    "title": row.get("Title", ""),
                    "_raw_rows": [],
                    "_tour_id": str(tour_id),
                    "_wholesale_id": str(wholesale_id),
                }
            programs[tour_id]["_raw_rows"].append(row)

        results = list(programs.values())
        logger.info(
            "Discovered %d programs (%d rows total, %s)",
            len(results),
            len(all_rows),
            f"country={country}" if country else "all countries",
        )
        return results

    # ------------------------------------------------------------------ #
    #  Tour parsing
    # ------------------------------------------------------------------ #

    def scrape_tour(self, url: str) -> dict | None:
        """Not used for API-based flow."""
        logger.warning("scrape_tour() called directly — use discover_tours() flow")
        return None

    def scrape_program(self, tour_info: dict) -> dict | None:
        """Parse a tour program from pre-fetched API data."""
        rows = tour_info.get("_raw_rows", [])
        if not rows:
            return None

        first = rows[0]

        # Basic info
        title = first.get("Title", "")
        product_code = first.get("code_package", "")
        country = first.get("CountryEn", "")

        # Duration
        days = self._to_int(first.get("numday"))
        nights = self._to_int(first.get("numnight"))

        # Price (minimum across all rows)
        price_from = self._to_decimal(first.get("MintourPrice"))

        # Airline
        airline_code = first.get("AirlineIATA", "")

        # Images
        hero_image_url = first.get("CoverImage", "")
        banner_url = first.get("bannerAds", "")

        # Description
        highlight = first.get("Description", "")

        # Detail page URL
        tour_id = first.get("TourID", "")
        wholesale_id = first.get("wholesale_id", "")
        source_url = (
            f"{self.base_url}/tour/{country}/"
            f"{first.get('tour_id', '')}-{tour_id}-{wholesale_id}"
        )

        # Parse departures from LoadTour rows
        departures = []
        for row in rows:
            dep = self._parse_departure_from_row(row)
            if dep:
                departures.append(dep)

        # Optionally fetch full period data for more pricing detail
        if tour_id and wholesale_id:
            try:
                extra_deps = self._fetch_periods(str(tour_id), str(wholesale_id))
                if extra_deps and len(extra_deps) > len(departures):
                    departures = extra_deps
            except Exception as e:
                logger.debug("Period fetch failed for %s: %s", product_code, e)

        # Images list
        images = []
        if hero_image_url:
            images.append(hero_image_url)
        if banner_url and banner_url != hero_image_url:
            images.append(banner_url)

        data = {
            "title": title,
            "title_th": first.get("Title", title),
            "product_code": product_code,
            "duration_days": days,
            "duration_nights": nights,
            "price_from": price_from,
            "destination_name": country,
            "airline_code": airline_code,
            "highlight": highlight,
            "highlight_th": highlight,
            "source": "go365",
            "source_url": source_url,
            "external_id": str(tour_id),
            "hero_image_url": hero_image_url,
            "pdf_url": "",  # PDF URLs from periods
            # Related data
            "_departures": departures,
            "_images": images,
            "_itinerary": [],  # Not available from API
            "_flights": [],
        }

        # Set PDF URL from first period that has one
        for dep in departures:
            pdf = dep.pop("_pdf_url", "")
            if pdf and not data["pdf_url"]:
                data["pdf_url"] = pdf

        return data

    # ------------------------------------------------------------------ #
    #  Departure parsing from LoadTour rows
    # ------------------------------------------------------------------ #

    def _parse_departure_from_row(self, row: dict) -> dict | None:
        """Parse one departure from a LoadTour row."""
        dep_date = self._parse_datetime(row.get("MinDate_departing"))
        ret_date = self._parse_datetime(row.get("MaxDate_departing"))

        if not dep_date:
            return None

        price_adult = self._to_decimal(row.get("tourPrice"))

        # Discount
        price_adult_promo = None
        price_dc = self._to_decimal(row.get("tourPriceDC"))
        if price_dc and price_adult and price_dc < price_adult:
            price_adult_promo = price_dc

        # Status
        seat_confirm = row.get("seat_confirm")
        status = "available"
        if seat_confirm == 0 or seat_confirm == "0":
            status = "soldout"

        return {
            "departure_date": dep_date,
            "return_date": ret_date or dep_date,
            "price_adult": price_adult,
            "price_adult_promo": price_adult_promo,
            "status": status,
            "period_code": row.get("tourCode", ""),
        }

    # ------------------------------------------------------------------ #
    #  Full period data (per-tour API call)
    # ------------------------------------------------------------------ #

    def _fetch_periods(self, tour_id: str, wholesale_id: str) -> list[dict]:
        """Fetch detailed period data for a specific tour."""
        periods_json = self._fetch_encrypted(
            "/search/LoadPeriodListDate",
            {"TourID": tour_id, "wholesale_id": wholesale_id},
        )
        data = json.loads(periods_json)
        result = data.get("result", [])

        departures = []
        for period in result:
            dep = self._parse_period(period)
            if dep:
                departures.append(dep)

        return departures

    def _parse_period(self, period: dict) -> dict | None:
        """Parse one period from LoadPeriodListDate response."""
        dep_date = self._parse_datetime(period.get("tourDate_departing"))
        ret_date = self._parse_datetime(period.get("tourDate_returning"))

        if not dep_date:
            return None

        price_adult = self._to_decimal(period.get("tourPrice"))

        # Status from available + visible
        available = period.get("available", 1)
        visible = period.get("visible")
        status = "available"
        if available == 0 or available == "0":
            status = "soldout"
        elif visible == "0":
            status = "closed"

        # Discount
        price_adult_promo = None
        discount = self._to_decimal(period.get("discountPrice"))
        if discount and price_adult and discount > 0:
            price_adult_promo = price_adult - discount

        # Capacity
        quota = self._to_int(period.get("quota"))
        seat_hold = self._to_int(period.get("seatHold")) or 0
        seat_tl = self._to_int(period.get("seatTL")) or 0
        booked = seat_hold + seat_tl if quota else None

        # PDF — fileNameListPDF may be an absolute URL or a bare filename
        pdf_file = period.get("fileNameListPDF", "")
        pdf_url = ""
        if pdf_file:
            if pdf_file.startswith("http"):
                pdf_url = pdf_file
            else:
                pdf_url = f"https://www.qualityb2bpackage.com/upload_doc/{pdf_file}"

        return {
            "departure_date": dep_date,
            "return_date": ret_date or dep_date,
            "price_adult": price_adult,
            "price_adult_promo": price_adult_promo,
            "status": status,
            "period_code": period.get("tourCode", ""),
            "group_size": quota,
            "booked": booked,
            "_pdf_url": pdf_url,
        }

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _parse_datetime(self, dt_str):
        """Parse '2026-03-03 00:00:00' → date."""
        if not dt_str:
            return None
        try:
            return datetime.strptime(dt_str[:10], "%Y-%m-%d").date()
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
            return int(str(val).strip())
        except (ValueError, TypeError):
            return None
