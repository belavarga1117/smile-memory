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

# Junk UI text that leaks into highlight/description (same as Zego portal)
_GS25_JUNK_RE = [
    re.compile(r"[×✕]\s*ส่งโปรแกรมทัวร์.*", re.DOTALL),
    re.compile(r"Email\s+ผู้รับ.*", re.DOTALL),
    re.compile(r"\bClose\s+Send\b.*", re.DOTALL),
    re.compile(r"ส่งโปรแกรมทัวร์\s+Email.*", re.DOTALL),
    re.compile(r"py\s+text\b", re.IGNORECASE),
]

# IATA airline codes (2-letter) and airport codes (3-letter) at title start
_AIRLINE_PREFIX_RE = re.compile(r"^[A-Z]{2}\s+")
_AIRPORT_PREFIX_RE = re.compile(r"^[A-Z]{3}\s+")
# " BY TK", " BY EK", " BY XJ" etc. — airline code in middle of title
_BY_AIRLINE_RE = re.compile(r"\s+BY\s+[A-Z]{2}\b")

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

        GS25 (thaioutbound) actual URL pattern:
          /programs/{DESTINATION}/{PROGRAM_CODE} {AIRLINE} {ROUTE} {TITLE}
        Examples:
          /programs/VIETNAM/DAD47%20FD%20DMK%20DANANG%20BANA%20HILLS...
          /programs/JAPAN-HOKKAIDO/CTS33%20TG%20BKK%20HOKKAIDO...

        Exclude:
          /programs/search/... (booking search pages — duplicate links)
          /programs/nogroup/... (category aggregate pages)
        """
        results = []
        seen_ids: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Match /programs/{UPPERCASE-DESTINATION}/{SLUG}
            # Exclude /programs/search/ and /programs/nogroup/ subpaths
            match = re.search(
                r"/programs/(?!search(?:/|$)|nogroup(?:/|$))([A-Z][^/?#\s]*)/([^/?#]+)",
                href,
            )
            if not match:
                continue

            destination_segment = match.group(1)
            title_slug = urllib.parse.unquote(match.group(2))

            # Program code: uppercase letters + digits at start of title slug
            # e.g. "DAD47 FD DMK ..." → "DAD47", "CTS33 TG ..." → "CTS33"
            code_match = re.match(r"([A-Z]{2,5}\d+)", title_slug)
            ext_id = code_match.group(1) if code_match else title_slug[:20].strip()

            if not ext_id or ext_id in seen_ids:
                continue
            seen_ids.add(ext_id)

            url = self._abs_url(href)
            # Use the decoded title slug as display title (includes code + route + name)
            title = title_slug[:200] or f"GS25 {ext_id}"

            results.append(
                {
                    "url": url,
                    "external_id": ext_id,
                    "title": title,
                    "destination_hint": destination_segment,
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

        # Extract reliable fields directly from URL (the page has a sidebar with other
        # tours, so HTML parsing can pick up wrong values from adjacent tour data).
        # URL format: /programs/{DESTINATION}/{CODE} {AIRLINE} {ROUTE} {TITLE} {DUR}
        decoded_url = urllib.parse.unquote(url)

        # Destination: URL segment before the title slug
        dest_m = re.search(r"/programs/([^/]+)/", decoded_url)
        destination_from_url = (
            dest_m.group(1).replace("-", " ").title() if dest_m else ""
        )

        # Program code: e.g. DAD47, CTS33 — the unique ID for this tour
        code_m = re.search(r"/programs/[^/]+/([A-Z]{2,5}\d+)", decoded_url)
        ext_id = (
            code_m.group(1) if code_m else re.sub(r".*programs/", "", decoded_url)[:20]
        )

        # Duration: "3D2N" in URL slug is the most reliable source
        url_slug = re.sub(r".*/programs/[^/]+/", "", decoded_url)
        dur_m = re.search(r"(\d+)D(?:ays?)?/?(\d+)N(?:ights?)?", url_slug, re.I)
        duration_from_url = (
            (int(dur_m.group(1)), int(dur_m.group(2))) if dur_m else (None, None)
        )

        # Airline: first 2-letter code after program code (e.g. "DAD47 FD" → "FD")
        airline_m = re.match(r"[A-Z]{2,5}\d+\s+([A-Z]{2})\b", url_slug)
        airline_from_url = airline_m.group(1) if airline_m else ""

        title = self._parse_title(soup)
        if not title:
            # Fallback: use URL slug as title (always available, contains full Thai title)
            title = url_slug.strip()[:300]
        if not title:
            logger.warning("No title found at %s — skipping", url)
            return None
        # Strip product code, airline/airport codes, and BY XX from title
        title = self._clean_gs25_title(title, ext_id)

        # Use URL-derived values; fall back to HTML parsing only where URL lacks data
        product_code = ext_id  # ext_id IS the product code (e.g. DAD47)
        duration_days, duration_nights = duration_from_url
        if not duration_days:
            duration_days, duration_nights = self._parse_duration(soup)
        destination = destination_from_url or self._parse_destination(soup)
        airline_code = airline_from_url or self._parse_airline(soup)
        highlight = self._parse_highlight(soup)
        price_from = self._parse_price(soup)
        hero_image_url = self._parse_hero_image(soup)
        pdf_url = self._parse_pdf_url(soup)
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

    def _clean_gs25_title(self, title: str, product_code: str = "") -> str:
        """Strip product code, airline/airport IATA codes, and BY XX from GS25 title.

        Examples:
          "IST58 TURKIYE SIMPLY BY TK 9D7N บินตรง" → "TURKIYE SIMPLY 9D7N บินตรง"
          "NRT69 XJ DMK TOKYO TULIP 9D7N"          → "TOKYO TULIP 9D7N"
        """
        if not title:
            return title
        # Strip product code prefix (e.g. "IST58 " or "NRT69 ")
        if product_code and title.startswith(product_code):
            title = title[len(product_code) :].lstrip()
        # Strip leading 2-letter airline IATA code (e.g. "XJ ")
        title = _AIRLINE_PREFIX_RE.sub("", title)
        # Strip leading 3-letter airport IATA code (e.g. "DMK ")
        title = _AIRPORT_PREFIX_RE.sub("", title)
        # Strip " BY XX" pattern (e.g. " BY TK", " BY EK")
        title = _BY_AIRLINE_RE.sub("", title)
        return title.strip()

    def _parse_title(self, soup: BeautifulSoup) -> str:
        """Parse tour title from the detail page.

        GS25 (thaioutbound) uses <h3> for the program title, not <h1>.
        """
        # Primary: <h3> — thaioutbound platform uses this for program names
        h3 = soup.find("h3")
        if h3:
            text = h3.get_text(strip=True)
            if text and len(text) > 5:
                return text[:300]

        # Secondary: <h1> or <h2>
        for tag in ["h1", "h2"]:
            el = soup.find(tag)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 5:
                    return text[:300]

        # Fallback: extract from <title> tag (usually "GS25 GS25 TRAVEL SERVICE")
        # — not useful; return empty to trigger URL-based fallback in scrape_tour
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
        """Extract 2-letter airline IATA code.

        GS25 tables show airline as 'THAI AIR ASIA (FD)' — extract from parentheses.
        Fallback: look for standard flight number format like TG205.
        """
        text = soup.get_text()
        # GS25 format: "AIRLINE NAME (XX)" in departure table
        match = re.search(r"\(([A-Z]{2})\)", text)
        if match:
            return match.group(1)
        # Fallback: flight number format TG205, FD123, etc.
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
                    for junk_re in _GS25_JUNK_RE:
                        text = junk_re.sub("", text)
                    text = text.strip()
                    if text:
                        return text[:2000]

        return ""

    def _parse_price(self, soup: BeautifulSoup) -> Decimal | None:
        """Parse lowest starting price in THB from departure table.

        GS25 price column format: '14,999' or '14,999>10,999' (promo: take right side).
        Minimum price across all departure rows is used as price_from.
        """
        candidates: list[Decimal] = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            header_text = " ".join(
                th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])
            )
            if "ราคา" not in header_text and "price" not in header_text:
                continue

            for row in rows[1:]:
                cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                for cell in cols:
                    # Handle promo format: "14,999>10,999" — take the promo (right) price
                    if ">" in cell:
                        cell = cell.split(">")[-1]
                    price_m = re.search(r"(\d{1,3}(?:,\d{3})+)", cell)
                    if price_m:
                        try:
                            val = Decimal(price_m.group(1).replace(",", ""))
                            if 5000 < val < 500000:  # Reasonable tour price range
                                candidates.append(val)
                        except InvalidOperation:
                            pass

        if candidates:
            return min(candidates)

        # Fallback: any price-like number >= 5000 in page text
        text = soup.get_text()
        for m in re.finditer(r"(\d{1,3}(?:,\d{3})+)", text):
            try:
                val = Decimal(m.group(1).replace(",", ""))
                if 5000 < val < 500000:
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

    def _parse_pdf_url(self, soup: BeautifulSoup) -> str:
        """Parse program tour PDF URL.

        GS25 stores PDFs at /programs/files/programtour/{program_group_id}/program_pdf_{id}.
        The program_group_id is embedded in the programGroupModel JS variable on the page.
        Tours without departures (expired) won't have this variable → return "".
        """
        import json as _json

        for script in soup.find_all("script"):
            content = script.string or ""
            if (
                "programGroupModel" not in content
                or "selectedEntranceCity" not in content
            ):
                continue
            m = re.search(r"var programGroupModel\s*=\s*(\{.+?\});", content, re.DOTALL)
            if not m:
                continue
            try:
                pgm = _json.loads(m.group(1))
                first_key = next(iter(pgm), None)
                if not first_key or not pgm[first_key]:
                    continue
                pg_id = pgm[first_key][0].get("program_group_id")
                if pg_id:
                    return (
                        f"https://gs25travel.com/programs/files/programtour/"
                        f"{pg_id}/program_pdf_{pg_id}"
                    )
            except (ValueError, KeyError, IndexError):
                pass

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
                if len(cols) < 4:
                    continue

                texts = [col.get_text(strip=True) for col in cols]

                # GS25 table column order (0-indexed, first col is empty checkbox):
                # [0]=checkbox [1]=date_range [2]=duration [3]=program [4]=airline
                # [5]=price [6]=commission [7]=com_sell [8]=total_seats [9]=avail
                # [10]=status [11]=remark
                dep_date = None
                ret_date = None
                price_adult = None
                status = "available"

                # Column 1: date range "DD - DD MMM YYYY" or "DD/MM/YYYY"
                date_cell = texts[1] if len(texts) > 1 else ""
                dep_date, ret_date = self._parse_date_range(date_cell)

                # Column 5: price "14,999" or "14,999>10,999" (promo)
                price_cell = texts[5] if len(texts) > 5 else ""
                if ">" in price_cell:
                    price_cell = price_cell.split(">")[-1]  # Take promo price
                price_m = re.search(r"(\d{1,3}(?:,\d{3})+)", price_cell)
                if price_m:
                    try:
                        val = Decimal(price_m.group(1).replace(",", ""))
                        if val > 1000:
                            price_adult = val
                    except InvalidOperation:
                        pass

                # Column 10: status (English: Available, Waitlist, Full)
                status_cell = texts[10] if len(texts) > 10 else ""
                remark_cell = texts[11] if len(texts) > 11 else ""
                combined = f"{status_cell} {remark_cell}"
                if any(kw in combined for kw in ["Waitlist", "เต็ม", "Full", "Sold"]):
                    status = "soldout"
                elif any(kw in combined for kw in ["Cancel", "ยกเลิก", "Closed", "ปิด"]):
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

    def _parse_date_range(self, text: str) -> tuple[date | None, date | None]:
        """Parse GS25 date range cell: '07 - 09 Mar 2026' → (dep_date, ret_date)."""
        text = text.strip()
        if not text:
            return None, None

        # GS25 format: "07 - 09 Mar 2026"
        m = re.match(r"(\d{1,2})\s*[-–]\s*(\d{1,2})\s+([A-Za-z]{3})\s+(\d{4})", text)
        if m:
            day1, day2, mon_str, year_str = (
                m.group(1),
                m.group(2),
                m.group(3),
                m.group(4),
            )
            try:
                dep = datetime.strptime(
                    f"{day1} {mon_str} {year_str}", "%d %b %Y"
                ).date()
                ret = datetime.strptime(
                    f"{day2} {mon_str} {year_str}", "%d %b %Y"
                ).date()
                return dep, ret
            except ValueError:
                pass

        # Fallback: single date
        d = self._parse_date(text)
        return d, None
