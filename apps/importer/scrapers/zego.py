"""Zego Travel (zegotravel.com) tour API client.

Uses the Zego portal's internal API (not the public zegoapi.com v1.5).
Authentication via session cookies (agent login).

Data flow:
1. Login → get session cookies (agencyID, saleAdmin, saleCode)
2. POST /Programtourweb/list_view_by_web → all tours with departures, pricing, flights
3. GET /programtourweb/listprogramtourday?id={programtour_id} → itinerary per program

The listing endpoint returns one row per departure (TourID), grouped by programtour_id.
Multiple departures share the same program details (title, code, duration, etc.)
"""

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from decimal import Decimal, InvalidOperation
from http.cookiejar import CookieJar

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Meal icon mapping (Zego uses Font Awesome classes)
MEAL_ICON_MAP = {
    "fas fa-utensils": "Y",         # Regular meal
    "fas fa-plane airplane-day": "P",  # Plane meal
    "fas fa-plane": "P",
    "airplane-day": "P",
    "": "N",
}


class ZegoScraper(BaseScraper):
    """API client for Zego Travel portal.

    Uses the portal's internal API endpoints with session cookies.
    NOT a web scraper — makes structured API calls for clean JSON data.
    """

    source_name = "zego"
    base_url = "https://www.zegotravel.com"

    def __init__(self, username="", password="", **kwargs):
        super().__init__(min_delay=1.0, max_delay=2.0, max_retries=1)
        self._username = username
        self._password = password
        self._agency_id = ""
        self._sale_code = ""
        self._admin_id = "0"
        self._logged_in = False

    # ------------------------------------------------------------------ #
    #  Authentication
    # ------------------------------------------------------------------ #

    def _login(self):
        """Login to Zego portal and store session cookies."""
        if self._logged_in:
            return

        if not self._username or not self._password:
            raise ValueError(
                "Zego credentials required. Set ZEGO_USERNAME and ZEGO_PASSWORD "
                "environment variables or pass --zego-user and --zego-pass."
            )

        logger.info("Logging in to Zego as %s...", self._username)

        url = f"{self.base_url}/Registers/SaleAgencyLogin"
        model = json.dumps({
            "Username": self._username,
            "Password": self._password,
        })

        # Build multipart form data
        boundary = "----ZegoFormBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="model"\r\n\r\n'
            f"{model}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        response = self._opener.open(req, timeout=30)
        data = json.loads(response.read().decode("utf-8"))

        if not data or not isinstance(data, list) or not data[0].get("agencyID"):
            raise ValueError("Zego login failed — invalid credentials or response")

        agent = data[0]
        self._agency_id = str(agent["agencyID"])
        self._sale_code = str(agent["Sale_Agency_ID"])
        self._admin_id = str(agent.get("adminID", "0"))

        # Set cookies for subsequent requests
        for name, value in [
            ("ZegoAgencyCode", self._agency_id),
            ("ZegoSaleAdmin", self._admin_id),
            ("ZegoSaleCode", self._sale_code),
        ]:
            cookie = urllib.request.Request(self.base_url)
            self._cookie_jar.set_cookie(
                _make_cookie(name, value, ".zegotravel.com")
            )

        self._logged_in = True
        logger.info(
            "Logged in: agencyID=%s, saleCode=%s",
            self._agency_id, self._sale_code,
        )

    # ------------------------------------------------------------------ #
    #  Tour discovery (all tours from one API call)
    # ------------------------------------------------------------------ #

    def discover_tours(self, country=None) -> list[dict]:
        """Get all tours from Zego's listing API.

        Returns one entry per unique programtour_id (not per departure).
        """
        self._login()
        self._rate_limit()

        raw_data = self._fetch_tour_listing()

        # Group by programtour_id
        programs = {}
        for row in raw_data:
            pid = row.get("programtour_id", "")
            if not pid:
                continue

            # Filter by country if specified
            if country:
                row_country = row.get("Country_EN", "")
                if country.upper() != row_country.upper():
                    continue

            if pid not in programs:
                programs[pid] = {
                    "url": f"{self.base_url}/?s=true&p={row.get('programtour_code', '')}",
                    "external_id": pid,
                    "title": row.get("programtour_name", ""),
                    "_raw_rows": [],
                }
            programs[pid]["_raw_rows"].append(row)

        results = list(programs.values())
        logger.info(
            "Discovered %d programs (%d total departure rows)",
            len(results), len(raw_data),
        )
        return results

    def _fetch_tour_listing(self) -> list[dict]:
        """Fetch full tour listing from portal API."""
        url = f"{self.base_url}/Programtourweb/list_view_by_web"
        model = json.dumps({
            "date_f": "2000-01-01",
            "date_t": "2000-01-01",
            "str_search": "",
            "str_country": "",
        })

        boundary = "----ZegoFormBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="datamodel"\r\n\r\n'
            f"{model}\r\n"
            f"--{boundary}--\r\n"
        ).encode("utf-8")

        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Cookie": (
                f"ZegoAgencyCode={self._agency_id}; "
                f"ZegoSaleAdmin={self._admin_id}; "
                f"ZegoSaleCode={self._sale_code}"
            ),
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        response = self._opener.open(req, timeout=60)
        return json.loads(response.read().decode("utf-8"))

    def _fetch_itinerary(self, programtour_id: str) -> list[dict]:
        """Fetch day-by-day itinerary for a program."""
        url = (
            f"{self.base_url}/programtourweb/listprogramtourday"
            f"?id={urllib.parse.quote(programtour_id)}"
        )

        headers = {
            "Cookie": (
                f"ZegoAgencyCode={self._agency_id}; "
                f"ZegoSaleAdmin={self._admin_id}; "
                f"ZegoSaleCode={self._sale_code}"
            ),
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
        }

        req = urllib.request.Request(url, headers=headers)
        response = self._opener.open(req, timeout=30)
        return json.loads(response.read().decode("utf-8"))

    # ------------------------------------------------------------------ #
    #  Tour parsing (from raw API data)
    # ------------------------------------------------------------------ #

    def scrape_tour(self, url: str) -> dict | None:
        """Parse tour from raw API rows (pre-fetched by discover_tours).

        Unlike Go365/RealJourney, Zego data is already structured JSON.
        This method is called by the management command with url as the key,
        but the actual data comes from _raw_rows attached during discovery.
        """
        # This shouldn't be called directly — use scrape_program() instead
        logger.warning("scrape_tour() called directly — use scrape_all_programs()")
        return None

    def scrape_program(self, tour_info: dict) -> dict | None:
        """Parse a program from pre-fetched raw API data.

        Args:
            tour_info: dict from discover_tours() with _raw_rows
        """
        rows = tour_info.get("_raw_rows", [])
        if not rows:
            return None

        # Use first row for program-level data
        first = rows[0]

        # Program info
        product_code = first.get("programtour_code", "")
        title = first.get("programtour_name", "")
        full_title = first.get("Tour_Name", title)
        country = first.get("Country_EN", "")

        # Duration
        days, nights = self._parse_duration(first.get("duration", ""))

        # Starting price (from the programtour level)
        price_from = self._to_decimal(first.get("start_price"))

        # Hotel stars
        hotel_min = self._to_int(first.get("minStar"))
        hotel_max = self._to_int(first.get("maxStar"))

        # Meals
        total_meals = self._to_int(first.get("totalMeals"))
        plane_meals = first.get("planeMeals", "0") != "0"

        # Highlight
        highlight = first.get("highlight", "")

        # Hero image
        pg_image = first.get("pg_image", "")
        hero_image_url = ""
        if pg_image:
            hero_image_url = f"{self.base_url}/images/image_programtour/{pg_image}"

        # PDF/Word
        pdf_file = first.get("upload_pdf", "")
        pdf_url = ""
        if pdf_file:
            pdf_url = f"{self.base_url}/uploadfile/p_d_f/programtour/{pdf_file}"

        word_file = first.get("upload_word", "")
        word_url = ""
        if word_file:
            word_url = f"{self.base_url}/uploadfile/word/programtour/{word_file}"

        # Locations
        locations = self._parse_locations(first.get("location", ""))

        # Parse departures from ALL rows
        departures = []
        airline_code = ""
        for row in rows:
            dep = self._parse_departure(row)
            if dep:
                departures.append(dep)
            # Get airline from flight data
            if not airline_code:
                airline_code = self._parse_airline_from_flights(row)

        # Fetch itinerary (one API call per program)
        programtour_id = first.get("programtour_id", "")
        itinerary = []
        if programtour_id:
            try:
                self._rate_limit()
                raw_days = self._fetch_itinerary(programtour_id)
                itinerary = self._parse_itinerary(raw_days)
            except Exception as e:
                logger.warning("Failed to fetch itinerary for %s: %s", product_code, e)

        data = {
            "title": full_title or title,
            "title_th": title,
            "product_code": product_code,
            "duration_days": days,
            "duration_nights": nights,
            "price_from": price_from,
            "destination_name": country.title() if country else "",
            "airline_code": airline_code,
            "highlight": highlight,
            "highlight_th": highlight,
            "hotel_stars_min": hotel_min,
            "hotel_stars_max": hotel_max,
            "total_meals": total_meals,
            "plane_meals": plane_meals,
            "locations": locations,
            "source": "zego",
            "source_url": f"{self.base_url}/?s=true&p={product_code}",
            "external_id": programtour_id,
            "hero_image_url": hero_image_url,
            "pdf_url": pdf_url,
            "word_url": word_url,
            "_departures": departures,
            "_itinerary": itinerary,
            "_images": [hero_image_url] if hero_image_url else [],
            "_flights": [],
        }

        return data

    # ------------------------------------------------------------------ #
    #  Departure parsing
    # ------------------------------------------------------------------ #

    def _parse_departure(self, row: dict) -> dict | None:
        """Parse one departure row from the listing API."""
        start_date = self._parse_date(row.get("Start_date"))
        end_date = self._parse_date(row.get("End_date"))

        if not start_date:
            return None

        price_adult = self._to_decimal(row.get("Price"))
        if not price_adult or price_adult <= 0:
            price_adult = self._to_decimal(row.get("adultRegularPrice"))

        # Status mapping
        tour_status = row.get("Tour_Status", "N")
        status_sold = row.get("status_sold_out", "O")
        close_status = row.get("close_status", "N")

        if close_status == "Y":
            status = "closed"
        elif status_sold == "S":
            status = "soldout"
        elif tour_status == "C":
            status = "closed"
        else:
            status = "available"

        dep = {
            "departure_date": start_date,
            "return_date": end_date or start_date,
            "price_adult": price_adult,
            "status": status,
            "period_code": row.get("Tour_code", ""),
            "bus": row.get("Bus", ""),
            # Extra pricing from Zego
            "price_child": self._to_decimal(row.get("infantRegularPrice")),
            "price_single_supplement": self._to_decimal(row.get("singleRegularPrice")),
            "price_join_land": self._to_decimal(row.get("joinLandRegularPrice")),
            "deposit": self._to_decimal(row.get("regularDeposit")),
            # Promo pricing
            "price_adult_promo": self._to_decimal(row.get("adultPromotionPrice")),
            "price_child_promo": self._to_decimal(row.get("infantPromotionPrice")),
            # Visa
            "price_single_visa": self._to_decimal(row.get("visaRegularPrice")),
            # Commission (internal)
            "commission": row.get("com_standard", ""),
            # Capacity
            "group_size": self._to_int(row.get("Seat")),
            "booked": self._to_int(row.get("Booking")),
        }

        return dep

    # ------------------------------------------------------------------ #
    #  Itinerary parsing
    # ------------------------------------------------------------------ #

    def _parse_itinerary(self, raw_days: list[dict]) -> list[dict]:
        """Parse itinerary days from API response."""
        itinerary = []

        for i, day in enumerate(raw_days, 1):
            # Title is the day number as string
            title = f"Day {day.get('pgt_day_title', i)}"

            # Description (HTML content)
            desc_html = day.get("pgt_day_des", "")
            description = self._html_to_text(desc_html)

            # Meals (Zego uses Font Awesome icon classes)
            breakfast = self._parse_meal_icon(day.get("pgt_morning", ""))
            lunch = self._parse_meal_icon(day.get("pgt_midday", ""))
            dinner = self._parse_meal_icon(day.get("pgt_evening", ""))

            # Meal descriptions
            breakfast_desc = day.get("pgt_morning_des", "")
            lunch_desc = day.get("pgt_midday_des", "")
            dinner_desc = day.get("pgt_evening_des", "")

            # Hotel
            hotel = day.get("pgt_hotel", "")
            equivalent = day.get("pgt_equivalent", "")
            hotel_name = hotel
            if equivalent:
                hotel_name = f"{hotel} ({equivalent})"

            itinerary.append({
                "day_number": i,
                "title": title,
                "description": description,
                "hotel": hotel_name.strip()[:300],
                "meals": {
                    "breakfast": breakfast,
                    "lunch": lunch,
                    "dinner": dinner,
                },
                "breakfast_description": breakfast_desc[:300],
                "lunch_description": lunch_desc[:300],
                "dinner_description": dinner_desc[:300],
            })

        return itinerary

    def _parse_meal_icon(self, icon_class: str) -> str:
        """Convert Zego meal icon class to Y/N/P."""
        if not icon_class or not icon_class.strip():
            return "N"
        icon = icon_class.strip()
        # Check known mappings
        for key, val in MEAL_ICON_MAP.items():
            if key and key in icon:
                return val
        # If it has any icon class, assume meal is included
        if "fa-" in icon or "fas" in icon:
            return "Y"
        return "N"

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _parse_duration(self, duration_str: str) -> tuple[int | None, int | None]:
        """Parse 'X วัน Y คืน' → (days, nights)."""
        if not duration_str:
            return None, None
        match = re.search(r"(\d+)\s*วัน\s*(\d+)\s*คืน", duration_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"(\d+)\s*[Dd](?:ays?)?\s*(\d+)\s*[Nn]", duration_str)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def _parse_date(self, date_str: str):
        """Parse 'YYYY-MM-DD HH:MM:SS' → date."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _parse_locations(self, location_str: str) -> list[str]:
        """Parse JSON location array → list of city names."""
        if not location_str:
            return []
        try:
            locs = json.loads(location_str)
            return [loc.get("en", loc.get("th", "")) for loc in locs if loc]
        except (json.JSONDecodeError, TypeError):
            return []

    def _parse_airline_from_flights(self, row: dict) -> str:
        """Extract airline IATA code from flight JSON."""
        flights_str = row.get("flights", "")
        if not flights_str:
            flights_str = row.get("flight_connections", "")
        if not flights_str:
            return ""
        try:
            flights = json.loads(flights_str)
            if flights and isinstance(flights, list):
                flight_num = flights[0].get("Flight", "")
                # Extract airline code (first 2 chars of flight number)
                match = re.match(r"([A-Z]{2})\d", flight_num)
                if match:
                    return match.group(1)
        except (json.JSONDecodeError, TypeError):
            pass
        return ""

    def _html_to_text(self, html: str) -> str:
        """Strip HTML tags and convert to plain text."""
        if not html:
            return ""
        # Remove HTML tags
        text = re.sub(r"<br\s*/?>", "\n", html)
        text = re.sub(r"<[^>]+>", "", text)
        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&ndash;", "–")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        return text.strip()

    def _to_decimal(self, val) -> Decimal | None:
        """Convert string/number to Decimal, handling edge cases."""
        if val is None or val == "" or val == "0" or val == "0.000":
            return None
        try:
            d = Decimal(str(val).replace(",", "").strip())
            return d if d > 0 else None
        except (InvalidOperation, ValueError):
            return None

    def _to_int(self, val) -> int | None:
        """Convert string/number to int."""
        if val is None or val == "":
            return None
        try:
            return int(str(val).strip())
        except (ValueError, TypeError):
            return None


def _make_cookie(name, value, domain):
    """Create a cookie for urllib cookie jar."""
    import http.cookiejar
    return http.cookiejar.Cookie(
        version=0, name=name, value=value,
        port=None, port_specified=False,
        domain=domain, domain_specified=True, domain_initial_dot=True,
        path="/", path_specified=True,
        secure=False, expires=None, discard=True,
        comment=None, comment_url=None,
        rest={}, rfc2109=False,
    )
