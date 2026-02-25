"""Unit tests for Go365, Real Journey, and GS25 scraper helper methods.

These test pure data-transformation logic (no HTTP calls) — the internal
_parse_*, _to_decimal, _format_product_code etc. methods.
"""

from datetime import date
from decimal import Decimal


class TestGo365ScraperHelpers:
    """Unit tests for Go365Scraper internal methods."""

    def _scraper(self):
        from apps.importer.scrapers.go365 import Go365Scraper

        return Go365Scraper(api_key="test-key")

    def test_to_decimal_normal_value(self):
        s = self._scraper()
        assert s._to_decimal("29900") == Decimal("29900")

    def test_to_decimal_with_comma(self):
        s = self._scraper()
        assert s._to_decimal("29,900") == Decimal("29900")

    def test_to_decimal_zero_returns_none(self):
        s = self._scraper()
        assert s._to_decimal(0) is None
        assert s._to_decimal("0") is None

    def test_to_decimal_none_returns_none(self):
        s = self._scraper()
        assert s._to_decimal(None) is None
        assert s._to_decimal("") is None

    def test_to_int_normal(self):
        s = self._scraper()
        assert s._to_int("5") == 5
        assert s._to_int(3) == 3

    def test_to_int_none_returns_none(self):
        s = self._scraper()
        assert s._to_int(None) is None
        assert s._to_int("") is None

    def test_parse_departure_from_row_valid(self):
        s = self._scraper()
        row = {
            "MinDate_departing": "2026-06-01",
            "MaxDate_departing": "2026-06-05",
            "tourPrice": "29900",
            "seat_confirm": 1,
        }
        result = s._parse_departure_from_row(row)
        assert result is not None
        assert result["price_adult"] == Decimal("29900")
        assert result["status"] == "available"

    def test_parse_departure_from_row_soldout(self):
        s = self._scraper()
        row = {
            "MinDate_departing": "2026-06-01",
            "tourPrice": "29900",
            "seat_confirm": 0,
        }
        result = s._parse_departure_from_row(row)
        assert result["status"] == "soldout"

    def test_parse_departure_from_row_promo_price(self):
        """Discounted price (tourPriceDC < tourPrice) sets price_adult_promo."""
        s = self._scraper()
        row = {
            "MinDate_departing": "2026-06-01",
            "tourPrice": "29900",
            "tourPriceDC": "24900",
            "seat_confirm": 1,
        }
        result = s._parse_departure_from_row(row)
        assert result["price_adult_promo"] == Decimal("24900")

    def test_parse_departure_from_row_no_date_returns_none(self):
        s = self._scraper()
        result = s._parse_departure_from_row({"tourPrice": "29900"})
        assert result is None

    def test_parse_period_valid(self):
        s = self._scraper()
        period = {
            "tourDate_departing": "2026-06-01",
            "tourDate_returning": "2026-06-05",
            "tourPrice_Adult": "29900",
            "seat_confirm": 1,
        }
        result = s._parse_period(period)
        assert result is not None
        assert result["departure_date"] == date(2026, 6, 1)


class TestRealJourneyScraperHelpers:
    """Unit tests for RealJourneyScraper internal methods."""

    def _scraper(self):
        from apps.importer.scrapers.realjourney import RealJourneyScraper

        return RealJourneyScraper()

    def test_to_decimal_normal(self):
        s = self._scraper()
        assert s._to_decimal("19900") == Decimal("19900")

    def test_to_decimal_zero_returns_none(self):
        s = self._scraper()
        assert s._to_decimal(0) is None

    def test_to_int_normal(self):
        s = self._scraper()
        assert s._to_int(5) == 5

    def test_parse_iso_date_valid(self):
        s = self._scraper()
        result = s._parse_iso_date("2026-04-01T00:00:00")
        assert result == date(2026, 4, 1)

    def test_parse_iso_date_with_z(self):
        s = self._scraper()
        result = s._parse_iso_date("2026-04-01T00:00:00Z")
        assert result == date(2026, 4, 1)

    def test_parse_iso_date_none_returns_none(self):
        s = self._scraper()
        assert s._parse_iso_date(None) is None
        assert s._parse_iso_date("") is None

    def test_parse_iso_date_invalid_returns_none(self):
        s = self._scraper()
        assert s._parse_iso_date("not-a-date") is None

    def test_format_product_code(self):
        s = self._scraper()
        assert s._format_product_code("RJHUCKG01") == "RJ-HUCKG01"

    def test_format_product_code_already_formatted(self):
        s = self._scraper()
        # Should not double-prefix
        result = s._format_product_code("RJ-HUCKG01")
        assert result == "RJ-HUCKG01"

    def test_format_product_code_empty(self):
        s = self._scraper()
        assert s._format_product_code("") == ""

    def test_thai_country_to_english_japan(self):
        s = self._scraper()
        assert s._thai_country_to_english("ญี่ปุ่น") == "Japan"

    def test_thai_country_to_english_unknown(self):
        s = self._scraper()
        assert s._thai_country_to_english("ประเทศใหม่") == "ประเทศใหม่"

    def test_thai_country_to_english_korea(self):
        s = self._scraper()
        assert s._thai_country_to_english("เกาหลี") == "South Korea"
