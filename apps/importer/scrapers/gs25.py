"""GS25 Travel (gs25travel.com) tour scraper.

Thai B2B travel portal built on the thaioutbound platform (Laravel PHP).
Uses session-based auth (CSRF token) + BeautifulSoup HTML parsing.

NOTE: HTML scrapers are inherently less reliable than JSON API scrapers.
      If the site HTML structure changes, the parser methods below will need
      adjusting. First-run logs show exactly what was found / not found.

Data flow:
1. GET /login → extract CSRF token (Laravel meta tag or hidden input)
2. POST /login with credentials → receive session cookies
3. GET /programs → tour listing (with pagination)
4. GET /programs/{id} → tour detail page → parse title, duration, departures, pricing
"""

import logging
import re
import urllib.parse
import urllib.request
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)

# Thai month abbreviations → month number (for departure date parsing)
THAI_MONTHS = {
    "มกราคม": 1,
    "กุมภาพันธ์": 2,
    "มีนาคม": 3,
    "เมษายน": 4,
    "พฤษภาคม": 5,
    "มิถุนายน": 6,
    "กรกฎาคม": 7,
    "สิงหาคม": 8,
    "กันยายน": 9,
    "ตุลาคม": 10,
    "พฤศจิกายน": 11,
    "ธันวาคม": 12,
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}


class GS25Scraper(BaseScraper):
    """HTML scraper for GS25 Travel B2B portal (thaioutbound platform).

    Rate limiting: 2–5s between requests to avoid account banning.
    Session-based auth: one login per scrape run, cookies maintained.
    """

    source_name = "gs25"
    base_url = "https://gs25travel.com"

    # Polite delays — longer than other scrapers to avoid IP/account bans
    def __init__(self, username="", password="", **kwargs):
        super().__init__(min_delay=2.5, max_delay=5.0, max_retries=2)
        self._username = username
        self._password = password
        self._logged_in = False

    # ------------------------------------------------------------------ #
    #  Authentication
    # ------------------------------------------------------------------ #

    def _get_csrf_token(self, soup: BeautifulSoup) -> str:
        """Extract Laravel CSRF token from a page."""
        # Standard Laravel: <meta name="csrf-token" content="...">
        meta = soup.find("meta", attrs={"name": "csrf-token"})
        if meta and meta.get("content"):
            return meta["content"]

        # Blade @csrf directive: <input type="hidden" name="_token" value="...">
        token_input = soup.find("input", attrs={"name": "_token"})
        if token_input and token_input.get("value"):
            return token_input["value"]

        raise ValueError(
            "CSRF token not found on GS25 login page — "
            "page structure may have changed. Check gs25travel.com/login manually."
        )

    def _login(self):
        """Login to GS25 portal and establish a session cookie."""
        if self._logged_in:
            return

        if not self._username or not self._password:
            raise ValueError(
                "GS25 credentials required. Set GS25_USERNAME and GS25_PASSWORD "
                "environment variables."
            )

        logger.info("Logging in to GS25 as %s...", self._username)

        # Step 1: GET /login → extract CSRF token
        login_url = f"{self.base_url}/login"
        soup = self._fetch(login_url)
        csrf_token = self._get_csrf_token(soup)
        logger.debug("Got CSRF token (first 12 chars): %s...", csrf_token[:12])

        # Step 2: POST credentials — try "email" field first (Laravel default),
        # then "username" if email login fails (some portals differ).
        self._rate_limit()

        # Thaioutbound platform may use "email" or "username" field
        # We try both by submitting under "email"; the portal accepts either.
        form_data = urllib.parse.urlencode(
            {
                "_token": csrf_token,
                "email": self._username,
                "password": self._password,
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": login_url,
            "Origin": self.base_url,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "th-TH,th;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        req = urllib.request.Request(
            login_url, data=form_data, headers=headers, method="POST"
        )
        response = self._opener.open(req, timeout=30)
        final_url = response.geturl()

        if "/login" in final_url:
            # Check if the portal uses "username" instead of "email"
            logger.warning(
                "Login with 'email' field failed, retrying with 'username' field..."
            )
            self._rate_limit()
            form_data2 = urllib.parse.urlencode(
                {
                    "_token": csrf_token,
                    "username": self._username,
                    "password": self._password,
                }
            ).encode("utf-8")
            req2 = urllib.request.Request(
                login_url, data=form_data2, headers=headers, method="POST"
            )
            response2 = self._opener.open(req2, timeout=30)
            final_url = response2.geturl()

            if "/login" in final_url:
                raise ValueError(
                    "GS25 login failed — check GS25_USERNAME and GS25_PASSWORD env vars. "
                    f"Tried fields: email and username. Final URL: {final_url}"
                )

        self._logged_in = True
        logger.info("GS25 login successful (redirected to: %s)", final_url)

    def _re_login_if_needed(self, soup: BeautifulSoup) -> bool:
        """Return True if the page looks like a login redirect."""
        if soup.find("form", action=re.compile(r"/login")):
            logger.warning("Session expired — re-logging in to GS25")
            self._logged_in = False
            self._login()
            return True
        return False

    # ------------------------------------------------------------------ #
    #  Tour discovery
    # ------------------------------------------------------------------ #

    def discover_tours(self, country=None) -> list[dict]:
        """Discover all tour program URLs from the GS25 portal."""
        self._login()

        results = []
        seen_urls: set[str] = set()

        # GS25 (thaioutbound platform) groups programs by category.
        # Login redirects to /programs/promotion — so the tour categories are
        # subpaths of /programs.  We scrape each known category in order.
        listing_paths = [
            "/programs/promotion",  # Login redirect lands here — most tours
            "/programs/regular",  # Regular (non-promo) programs
            "/programs/group",  # Group tours
            "/programs/package",  # Package tours
            "/programs",  # Root listing (may aggregate or redirect)
        ]

        found_any = False

        for path in listing_paths:
            try:
                soup = self._fetch(f"{self.base_url}{path}", referer=self.base_url)
                if self._re_login_if_needed(soup):
                    soup = self._fetch(f"{self.base_url}{path}", referer=self.base_url)

                links = self._extract_tour_links(soup)
                if links:
                    logger.info(
                        "Found %d tour links at %s%s", len(links), self.base_url, path
                    )
                    found_any = True
                    for link in links:
                        if link["url"] not in seen_urls:
                            seen_urls.add(link["url"])
                            results.append(link)
                    # Follow pagination for this category
                    results.extend(self._paginate(soup, seen_urls))
                else:
                    logger.debug(
                        "No tour links at %s%s — trying next path", self.base_url, path
                    )
            except Exception as e:
                logger.warning(
                    "Listing endpoint %s%s failed: %s", self.base_url, path, e
                )

        if not found_any:
            logger.error(
                "Could not find GS25 tour listing. Tried: %s. "
                "Browse gs25travel.com after login to find the correct tour list URL.",
                ", ".join(listing_paths),
            )
            return []

        # Country filter (post-discovery, since we can't filter before fetching)
        if country:
            country_lower = country.lower()
            filtered = [
                r for r in results if country_lower in r.get("title", "").lower()
            ]
            logger.info(
                "Country filter '%s': %d/%d tours", country, len(filtered), len(results)
            )
            results = filtered

        logger.info("Discovered %d GS25 tours total", len(results))
        return results

    def _extract_tour_links(self, soup: BeautifulSoup) -> list[dict]:
        """Extract tour program links from a listing page.

        GS25 URL patterns observed:
          /programs/promotion/549      ← category subpath + numeric ID
          /programs/regular/123        ← same pattern for other categories
          /programs/549                ← flat numeric ID (fallback)
        """
        results = []
        seen_ids: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Match /programs/{optional-category}/123
            match = re.search(r"/programs?/(?:[a-z]+/)?(\d+)", href)
            if not match:
                continue

            ext_id = match.group(1)
            if ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)

            url = self._abs_url(href)
            title = a.get_text(strip=True)[:200] or f"GS25 Program {ext_id}"

            results.append(
                {
                    "url": url,
                    "external_id": ext_id,
                    "title": title,
                }
            )

        return results

    def _paginate(self, first_page_soup: BeautifulSoup, seen_urls: set) -> list[dict]:
        """Follow pagination links to collect all tour URLs."""
        results = []

        next_link = first_page_soup.find(
            "a", attrs={"rel": "next"}
        ) or first_page_soup.find("a", string=re.compile(r"next|ต่อไป|›|»", re.I))

        page = 2
        while next_link and page <= 50:  # Safety cap at 50 pages
            href = next_link.get("href", "")
            if not href:
                break

            try:
                self._rate_limit()
                soup = self._fetch(self._abs_url(href))
                links = self._extract_tour_links(soup)
                new_links = [lnk for lnk in links if lnk["url"] not in seen_urls]

                if not new_links:
                    logger.debug(
                        "No new tour links on page %d — stopping pagination", page
                    )
                    break

                for link in new_links:
                    seen_urls.add(link["url"])
                    results.append(link)

                logger.debug("Page %d: +%d tours", page, len(new_links))

                next_link = soup.find("a", attrs={"rel": "next"}) or soup.find(
                    "a", string=re.compile(r"next|ต่อไป|›|»", re.I)
                )
                page += 1

            except Exception as e:
                logger.warning("Pagination failed at page %d: %s", page, e)
                break

        return results

    # ------------------------------------------------------------------ #
    #  Tour detail scraping
    # ------------------------------------------------------------------ #

    def scrape_tour(self, url: str) -> dict | None:
        """Scrape one tour detail page and return structured data."""
        self._login()

        soup = self._fetch(url, referer=f"{self.base_url}/programs")

        # Handle session expiry mid-scrape
        if self._re_login_if_needed(soup):
            soup = self._fetch(url, referer=f"{self.base_url}/programs")

        # Extract tour ID from URL
        match = re.search(r"/programs?/(\d+)", url)
        ext_id = match.group(1) if match else ""

        title = self._parse_title(soup)
        if not title:
            logger.warning("No title found at %s — skipping", url)
            return None

        product_code = self._parse_product_code(soup, ext_id)
        duration_days, duration_nights = self._parse_duration(soup)
        destination = self._parse_destination(soup)
        airline_code = self._parse_airline(soup)
        highlight = self._parse_highlight(soup)
        price_from = self._parse_price(soup)
        hero_image_url = self._parse_hero_image(soup)
        pdf_url = self._parse_pdf_url(soup, ext_id)
        departures = self._parse_departures(soup)

        logger.info(
            "Parsed: '%s' | %sD/%sN | dest=%s | %d departures | price=%s",
            title[:50],
            duration_days,
            duration_nights,
            destination or "?",
            len(departures),
            price_from,
        )

        return {
            "title": title,
            "title_th": title,
            "product_code": product_code,
            "duration_days": duration_days,
            "duration_nights": duration_nights,
            "price_from": price_from,
            "destination_name": destination,
            "airline_code": airline_code,
            "highlight": highlight,
            "highlight_th": highlight,
            "source": "gs25",
            "source_url": url,
            "external_id": ext_id,
            "hero_image_url": hero_image_url,
            "pdf_url": pdf_url,
            "_departures": departures,
            "_itinerary": [],  # Not parsed from HTML (complex multi-day layout)
            "_images": [hero_image_url] if hero_image_url else [],
            "_flights": [],
        }

    # ------------------------------------------------------------------ #
    #  Field parsers — tune these if HTML structure changes
    # ------------------------------------------------------------------ #

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse tour title from the detail page."""
        # Primary: first <h1> (most pages use this for the program name)
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(strip=True)
            if text and len(text) > 3:
                return text[:300]

        # Secondary: styled heading elements
        for tag, attrs in [
            ("h2", {"class": re.compile(r"title|program|tour|heading", re.I)}),
            (
                "div",
                {"class": re.compile(r"program-?name|tour-?title|page-?title", re.I)},
            ),
            ("h3", {}),
        ]:
            el = soup.find(tag, attrs) if attrs else soup.find(tag)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 3:
                    return text[:300]

        # Fallback: <title> tag minus "| GS25" suffix
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text(strip=True)
            cleaned = re.sub(
                r"\s*[\|–\-]\s*(GS25|gs25).*$", "", raw, flags=re.I
            ).strip()
            return (cleaned or raw)[:300]

        return ""

    def _parse_product_code(self, soup: BeautifulSoup, ext_id: str) -> str:
        """Parse program/product code."""
        text = soup.get_text()

        # Patterns common in Thai B2B tour portals
        for pattern in [
            r"(?:รหัส|โปรแกรม|Code)[:\s]+([A-Z0-9\-]{3,25})",
            r"\b(GS[-_]?\d{2,}[-_]?[A-Z0-9]{0,15})\b",
            r"\b([A-Z]{2,4}\d{3,6}[A-Z]{0,4})\b",  # e.g. JPN001, TW-006
        ]:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()[:50]

        # Use the site ID as a unique code prefix
        return f"GS25-{ext_id}" if ext_id else ""

    def _parse_duration(self, soup: BeautifulSoup) -> tuple[int | None, int | None]:
        """Parse duration from '7 วัน 6 คืน' or '7D/6N' patterns."""
        text = soup.get_text()

        for pattern in [
            r"(\d+)\s*วัน\s*(\d+)\s*คืน",
            r"(\d+)\s*D(?:ays?)?\s*/?\s*(\d+)\s*N(?:ights?)?",
            r"(\d+)\s*[Dd]ay[s]?\s+(\d+)\s*[Nn]ight[s]?",
        ]:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1)), int(match.group(2))

        return None, None

    def _parse_destination(self, soup: BeautifulSoup) -> str:
        """Parse destination from breadcrumb or page content."""
        # Try breadcrumb navigation (common in thaioutbound portals)
        for breadcrumb_el in soup.find_all(
            ["nav", "ol", "ul", "div"],
            attrs={"class": re.compile(r"breadcrumb", re.I)},
        ):
            items = [
                i.get_text(strip=True)
                for i in breadcrumb_el.find_all(["a", "li", "span"])
                if i.get_text(strip=True)
            ]
            # Second-to-last item is usually the country/category
            if len(items) >= 2:
                return items[-2][:100]

        # Fallback: scan for known country names in text
        text = soup.get_text()
        countries = [
            "Japan",
            "China",
            "Korea",
            "Taiwan",
            "Hong Kong",
            "Singapore",
            "Vietnam",
            "Malaysia",
            "Indonesia",
            "Europe",
            "Australia",
            "New Zealand",
            "India",
            "Turkey",
            "Switzerland",
            "Italy",
            "France",
            "Germany",
            "England",
            "ญี่ปุ่น",
            "จีน",
            "เกาหลี",
            "ยุโรป",
            "ไต้หวัน",
            "ฮ่องกง",
        ]
        for country in countries:
            if country in text:
                return country

        return ""

    def _parse_airline(self, soup: BeautifulSoup) -> str:
        """Extract 2-letter airline IATA code from flight numbers on the page."""
        text = soup.get_text()
        # Look for standard flight number format: TG205, EK101, etc.
        match = re.search(r"\b([A-Z]{2})\d{3,4}\b", text)
        if match:
            return match.group(1)
        return ""

    def _parse_highlight(self, soup: BeautifulSoup) -> str:
        """Parse tour description/highlights."""
        for tag, attrs in [
            (
                "div",
                {
                    "class": re.compile(
                        r"description|highlight|overview|content|detail", re.I
                    )
                },
            ),
            (
                "div",
                {"id": re.compile(r"description|highlight|overview|content", re.I)},
            ),
            ("section", {"class": re.compile(r"description|overview|highlight", re.I)}),
        ]:
            el = soup.find(tag, attrs)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if text and len(text) > 20:
                    return text[:2000]

        return ""

    def _parse_price(self, soup: BeautifulSoup) -> Decimal | None:
        """Parse starting price in THB."""
        text = soup.get_text()

        for pattern in [
            r"(?:เริ่มต้น|เริ่ม|ราคา|ผู้ใหญ่)[^\d]{0,10}(\d{1,3}(?:,\d{3})*)",
            r"(\d{1,3}(?:,\d{3})+)\s*(?:บาท|THB|฿)",
            r"(?:from|starting|Adult\s*price)[^\d]{0,10}(\d{1,3}(?:,\d{3})*)",
        ]:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    val = Decimal(match.group(1).replace(",", ""))
                    if val > 1000:  # Reasonable tour price floor
                        return val
                except InvalidOperation:
                    pass

        return None

    def _parse_hero_image(self, soup: BeautifulSoup) -> str:
        """Parse the main tour cover image URL."""
        # Prefer images with descriptive src paths
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            if any(
                kw in src.lower()
                for kw in ["cover", "banner", "program", "tour", "header"]
            ):
                if src.startswith("http"):
                    return src
                return self._abs_url(src)

        # Fallback: first non-icon image
        for img in soup.find_all("img", src=True):
            src = img.get("src", "")
            if src and not any(
                kw in src.lower()
                for kw in ["logo", "icon", "arrow", "btn", "flag", "rating"]
            ):
                if src.startswith("http"):
                    return src
                return self._abs_url(src)

        return ""

    def _parse_pdf_url(self, soup: BeautifulSoup, ext_id: str) -> str:
        """Parse PDF download link for the program."""
        # Look for PDF link in the page
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if (
                "programtour" in href
                or href.lower().endswith(".pdf")
                or "pdf" in href.lower()
            ):
                return self._abs_url(href)

        # Fallback: construct from known GS25 URL pattern
        # (confirmed from search results: /assets/files/programtour/{id}/program_pdf_{id})
        if ext_id:
            return (
                f"{self.base_url}/assets/files/programtour"
                f"/{ext_id}/program_pdf_{ext_id}"
            )

        return ""

    def _parse_departures(self, soup: BeautifulSoup) -> list[dict]:
        """Parse departure dates and adult prices from tables on the page."""
        departures = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # Check if the table header mentions dates or prices
            header_text = " ".join(
                th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])
            )
            has_date_col = any(
                kw in header_text for kw in ["วัน", "date", "period", "เดินทาง", "ออกเดิน"]
            )
            has_price_col = any(
                kw in header_text for kw in ["ราคา", "price", "adult", "บาท", "฿"]
            )

            if not has_date_col and not has_price_col:
                continue

            logger.debug("Found departure table (%d rows) — parsing", len(rows) - 1)

            for row in rows[1:]:
                cols = row.find_all(["td", "th"])
                if len(cols) < 2:
                    continue

                texts = [col.get_text(strip=True) for col in cols]
                dep_date = None
                ret_date = None
                price_adult = None
                status = "available"

                for text in texts:
                    # Try to parse as date
                    if dep_date is None:
                        parsed = self._parse_date(text)
                        if parsed:
                            dep_date = parsed
                            continue

                    # Second date becomes return date
                    if ret_date is None and dep_date is not None:
                        parsed = self._parse_date(text)
                        if parsed and parsed > dep_date:
                            ret_date = parsed
                            continue

                    # Price: look for numbers >= 1,000 (Thai tour price floor)
                    if price_adult is None:
                        price_match = re.search(r"(\d{1,3}(?:,\d{3})+|\d{5,})", text)
                        if price_match:
                            try:
                                val = Decimal(price_match.group(1).replace(",", ""))
                                if val > 1000:
                                    price_adult = val
                            except InvalidOperation:
                                pass

                    # Status keywords
                    if any(kw in text for kw in ["เต็ม", "Full", "Sold"]):
                        status = "soldout"
                    elif any(kw in text for kw in ["ยกเลิก", "Cancel", "ปิด", "Closed"]):
                        status = "closed"

                if dep_date and price_adult:
                    departures.append(
                        {
                            "departure_date": dep_date,
                            "return_date": ret_date or dep_date,
                            "price_adult": price_adult,
                            "status": status,
                            "period_code": "",
                        }
                    )

        if not departures:
            logger.debug(
                "No departure table parsed — tour will only have price_from (no departure dates)"
            )

        return departures

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _parse_date(self, text: str) -> date | None:
        """Parse a date string in various Thai/international formats."""
        text = text.strip()
        if not text or len(text) < 5:
            return None

        # Standard formats
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d %b %Y"]:
            try:
                return datetime.strptime(text, fmt).date()
            except (ValueError, AttributeError):
                pass

        # Thai month names (full or abbreviated)
        for thai_month, month_num in THAI_MONTHS.items():
            if thai_month in text:
                match = re.search(
                    r"(\d{1,2})\s*" + re.escape(thai_month) + r"\s*(\d{2,4})", text
                )
                if match:
                    day = int(match.group(1))
                    year = int(match.group(2))
                    if year < 100:
                        year += 2000
                    elif year > 2400:  # Buddhist Era
                        year -= 543
                    try:
                        return date(year, month_num, day)
                    except ValueError:
                        pass

        return None
