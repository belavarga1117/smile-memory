"""Field mapper — maps parsed source data to Django Tour model fields.

Supports:
1. Explicit field_mapping dict (admin configures per-import)
2. Auto-detection based on common column name patterns
"""

import logging
import re
from decimal import Decimal, InvalidOperation

from django.utils.text import slugify

logger = logging.getLogger(__name__)

# Common column name aliases → Django Tour model fields
# Each key is a Tour field, values are patterns that match source column names
AUTO_MAP = {
    # Tour basic fields
    "title": r"(tour_?name|program_?name|title|package_?name|ชื่อ.?ทัวร์|ชื่อ.?โปรแกรม)",
    "product_code": r"(product_?code|tour_?code|code|รหัส|program_?code)",
    "description": r"(description|detail|รายละเอียด|overview)",
    "short_description": r"(short_?desc|summary|สรุป)",
    "highlight": r"(highlight|ไฮไลท์|จุดเด่น)",
    # Classification
    "destination_name": r"(destination|country|ประเทศ|จุดหมาย)",
    "category_name": r"(category|type|ประเภท|หมวดหมู่)",
    "airline_code": r"(airline|สายการบิน|airline_?code|carrier)",
    # Duration
    "duration_days": r"(duration_?days|days|วัน|จำนวน.?วัน)",
    "duration_nights": r"(duration_?nights|nights|คืน)",
    # Pricing
    "price_from": r"(price|price_?from|ราคา|adult_?price|price_?adult|ราคา.?ผู้ใหญ่)",
    "price_child": r"(child_?price|price_?child|ราคา.?เด็ก)",
    # Departure
    "departure_date": r"(departure_?date|start_?date|วัน.?เดินทาง|depart)",
    "return_date": r"(return_?date|end_?date|วัน.?กลับ)",
    # Hotel
    "hotel_stars": r"(hotel_?stars?|star_?rating|ดาว|ระดับ.?โรงแรม)",
    # Meals
    "total_meals": r"(total_?meals|meals|มื้อ.?อาหาร)",
    # Includes/excludes
    "includes": r"(includes?|รวม|included)",
    "excludes": r"(excludes?|ไม่.?รวม|not_?included|excluded)",
    # Status
    "status": r"(status|สถานะ)",
    # Image URL
    "hero_image_url": r"(image_?url|hero_?image|รูป|photo)",
    # PDF
    "pdf_url": r"(pdf_?url|pdf|เอกสาร)",
}


class TourMapper:
    """Maps parsed row data to Tour model fields."""

    def __init__(self, field_mapping=None):
        """Initialize with optional explicit field_mapping dict."""
        self.field_mapping = field_mapping or {}

    def auto_detect_mapping(self, headers):
        """Guess field mapping from column headers using regex patterns.

        Returns:
            dict: {source_header: tour_field}
        """
        mapping = {}
        for header in headers:
            if not header:
                continue
            clean = header.lower().strip()
            for field, pattern in AUTO_MAP.items():
                if re.search(pattern, clean, re.IGNORECASE):
                    mapping[header] = field
                    break
        logger.info("Auto-detected mapping: %s", mapping)
        return mapping

    def get_effective_mapping(self, headers):
        """Return the mapping to use — explicit if set, otherwise auto-detect."""
        if self.field_mapping:
            return self.field_mapping
        return self.auto_detect_mapping(headers)

    def map_row(self, row_data, mapping):
        """Map a single parsed row to Tour-compatible field dict.

        Args:
            row_data: dict from parser (source_col: value)
            mapping: dict (source_col: django_field)

        Returns:
            dict with Tour model field names as keys.
        """
        mapped = {}
        for source_col, django_field in mapping.items():
            value = row_data.get(source_col, "")
            if value is None:
                value = ""

            # Type conversion based on target field
            converted = self._convert_value(django_field, value)
            if converted is not None:
                mapped[django_field] = converted

        # Post-processing: normalize fields that don't map 1:1 to Tour model
        # hotel_stars → hotel_stars_min + hotel_stars_max
        if "hotel_stars" in mapped:
            stars = mapped.pop("hotel_stars")
            if stars is not None:
                mapped["hotel_stars_min"] = stars
                mapped["hotel_stars_max"] = stars

        # Auto-generate slug if title present but slug isn't
        if "title" in mapped and "slug" not in mapped:
            base_slug = slugify(mapped["title"])
            if not base_slug and "product_code" in mapped:
                base_slug = slugify(mapped["product_code"])
            mapped["slug"] = base_slug or "imported-tour"

        return mapped

    def _convert_value(self, field_name, value):
        """Convert a raw value to the appropriate Python type for a Tour field."""
        if isinstance(value, str):
            value = value.strip()

        # Skip empty values for non-text fields
        if value == "" or value is None:
            return None

        # Integer fields
        if field_name in (
            "duration_days",
            "duration_nights",
            "hotel_stars",
            "total_meals",
        ):
            return self._to_int(value)

        # Decimal fields
        if field_name in ("price_from", "price_child"):
            return self._to_decimal(value)

        # Date fields
        if field_name in ("departure_date", "return_date"):
            return self._to_date(value)

        # Status mapping
        if field_name == "status":
            return self._map_status(value)

        # Everything else stays as string
        return str(value)

    def _to_int(self, value):
        """Convert value to int, stripping non-numeric chars."""
        if isinstance(value, (int, float)):
            return int(value)
        try:
            cleaned = re.sub(r"[^\d]", "", str(value))
            return int(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None

    def _to_decimal(self, value):
        """Convert value to Decimal, handling formatted numbers like 29,900."""
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        try:
            cleaned = re.sub(r"[^\d.]", "", str(value).replace(",", ""))
            return Decimal(cleaned) if cleaned else None
        except (InvalidOperation, ValueError):
            return None

    def _to_date(self, value):
        """Parse a date string into a date object."""
        from datetime import date, datetime

        if isinstance(value, (date, datetime)):
            return value if isinstance(value, date) else value.date()

        date_str = str(value).strip()
        # Try common formats
        for fmt in (
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%d %b %Y",
            "%d %B %Y",
        ):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        return None

    def _map_status(self, value):
        """Map various status strings to Tour.Status choices."""
        val = str(value).strip().lower()
        status_map = {
            "published": "published",
            "draft": "draft",
            "archived": "archived",
            "active": "published",
            "inactive": "archived",
            "เปิดขาย": "published",
            "ปิดขาย": "archived",
        }
        return status_map.get(val, "draft")
