"""Tests for importer app — mapper, parser, pipeline."""

from datetime import date
from decimal import Decimal

import pytest

from apps.importer.mappers.tour_mapper import TourMapper
from apps.importer.models import ImportJob
from apps.importer.parsers import get_parser
from apps.importer.parsers.base import ParseResult
from apps.importer.parsers.csv_parser import CsvParser
from apps.importer.pipeline import ImportPipeline
from apps.tours.models import Tour


# ── TourMapper Tests ──


class TestTourMapperAutoDetect:
    def setup_method(self):
        self.mapper = TourMapper()

    def test_auto_detect_title(self):
        mapping = self.mapper.auto_detect_mapping(["tour_name", "price", "days"])
        assert mapping["tour_name"] == "title"

    def test_auto_detect_price(self):
        mapping = self.mapper.auto_detect_mapping(["title", "price_from", "days"])
        assert mapping["price_from"] == "price_from"

    def test_auto_detect_destination(self):
        mapping = self.mapper.auto_detect_mapping(["title", "destination", "price"])
        assert mapping["destination"] == "destination_name"

    def test_auto_detect_duration(self):
        mapping = self.mapper.auto_detect_mapping(["title", "duration_days", "nights"])
        assert mapping["duration_days"] == "duration_days"
        assert mapping["nights"] == "duration_nights"

    def test_auto_detect_thai_columns(self):
        mapping = self.mapper.auto_detect_mapping(["ชื่อทัวร์", "ราคา", "ประเทศ"])
        assert mapping["ชื่อทัวร์"] == "title"
        assert mapping["ราคา"] == "price_from"
        assert mapping["ประเทศ"] == "destination_name"

    def test_no_match(self):
        mapping = self.mapper.auto_detect_mapping(["foo", "bar", "baz"])
        assert mapping == {}

    def test_explicit_mapping_overrides(self):
        mapper = TourMapper(field_mapping={"col_a": "title", "col_b": "price_from"})
        mapping = mapper.get_effective_mapping(["any", "headers"])
        assert mapping == {"col_a": "title", "col_b": "price_from"}


class TestTourMapperMapRow:
    def setup_method(self):
        self.mapper = TourMapper()

    def test_basic_mapping(self):
        mapping = {"name": "title", "code": "product_code"}
        row = {"name": "Japan Tour", "code": "JP-001"}
        result = self.mapper.map_row(row, mapping)
        assert result["title"] == "Japan Tour"
        assert result["product_code"] == "JP-001"
        assert "slug" in result

    def test_auto_slug_generation(self):
        mapping = {"name": "title"}
        row = {"name": "Amazing Japan Tour"}
        result = self.mapper.map_row(row, mapping)
        assert result["slug"] == "amazing-japan-tour"

    def test_no_slug_when_title_empty(self):
        """When title is empty, _convert_value returns None so title is not in mapped."""
        mapping = {"name": "title", "code": "product_code"}
        row = {"name": "", "code": "ZGTYO-001"}
        result = self.mapper.map_row(row, mapping)
        # title is empty → converted to None → not in mapped → no auto-slug
        assert "slug" not in result
        assert result["product_code"] == "ZGTYO-001"

    def test_slug_generated_with_title(self):
        mapping = {"name": "title", "code": "product_code"}
        row = {"name": "Japan Tour", "code": "ZGTYO-001"}
        result = self.mapper.map_row(row, mapping)
        assert result["slug"] == "japan-tour"

    def test_hotel_stars_normalization(self):
        mapping = {"stars": "hotel_stars"}
        row = {"stars": "4"}
        result = self.mapper.map_row(row, mapping)
        assert result["hotel_stars_min"] == 4
        assert result["hotel_stars_max"] == 4
        assert "hotel_stars" not in result


class TestTourMapperTypeConversion:
    def setup_method(self):
        self.mapper = TourMapper()

    def test_to_int(self):
        assert self.mapper._to_int(5) == 5
        assert self.mapper._to_int("7") == 7
        assert self.mapper._to_int("5 days") == 5
        assert self.mapper._to_int("") is None
        assert self.mapper._to_int(3.7) == 3

    def test_to_decimal(self):
        assert self.mapper._to_decimal(29900) == Decimal("29900")
        assert self.mapper._to_decimal("29,900") == Decimal("29900")
        assert self.mapper._to_decimal("29,900.50") == Decimal("29900.50")
        assert self.mapper._to_decimal("") is None
        assert self.mapper._to_decimal("฿29,900") == Decimal("29900")

    def test_to_date_iso(self):
        result = self.mapper._to_date("2025-03-15")
        assert result == date(2025, 3, 15)

    def test_to_date_slash(self):
        result = self.mapper._to_date("15/03/2025")
        assert result == date(2025, 3, 15)

    def test_to_date_obj(self):
        d = date(2025, 6, 1)
        assert self.mapper._to_date(d) == d

    def test_to_date_invalid(self):
        assert self.mapper._to_date("not a date") is None

    def test_map_status(self):
        assert self.mapper._map_status("published") == "published"
        assert self.mapper._map_status("active") == "published"
        assert self.mapper._map_status("inactive") == "archived"
        assert self.mapper._map_status("เปิดขาย") == "published"
        assert self.mapper._map_status("unknown") == "draft"


# ── CSV Parser Tests ──


class TestCsvParser:
    def test_parse_csv_string(self, tmp_path):
        csv_content = "tour_name,price,days\nJapan Tour,29900,5\nKorea Tour,19900,3\n"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)

        parser = CsvParser()
        result = parser.parse_file(str(csv_file))

        assert result.total_rows == 2
        assert "tour_name" in result.headers
        assert result.rows[0]["tour_name"] == "Japan Tour"
        assert result.rows[0]["price"] == "29900"

    def test_parse_csv_bytes(self):
        csv_bytes = b"title,price\nTest Tour,15000\n"
        parser = CsvParser()
        result = parser.parse_file(csv_bytes)
        assert result.total_rows == 1
        assert result.rows[0]["title"] == "Test Tour"

    def test_parse_csv_empty(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        parser = CsvParser()
        result = parser.parse_file(str(csv_file))
        assert result.total_rows == 0


class TestGetParser:
    def test_get_csv_parser(self):
        parser = get_parser("csv")
        assert isinstance(parser, CsvParser)

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_parser("xyz")


# ── ParseResult Tests ──


class TestParseResult:
    def test_total_rows(self):
        r = ParseResult(rows=[{"a": 1}, {"a": 2}])
        assert r.total_rows == 2

    def test_empty(self):
        r = ParseResult()
        assert r.total_rows == 0
        assert r.headers == []
        assert r.errors == []


# ── ImportJob Model Tests ──


class TestImportJobModel:
    def test_str(self, import_job):
        assert "Test Import" in str(import_job)
        assert "Zego" in str(import_job)

    def test_success_rate_no_rows(self, import_job):
        assert import_job.success_rate == 0

    def test_success_rate_all_success(self, import_job):
        import_job.rows_created = 8
        import_job.rows_updated = 2
        import_job.rows_failed = 0
        assert import_job.success_rate == 100.0

    def test_success_rate_partial(self, import_job):
        import_job.rows_created = 5
        import_job.rows_updated = 3
        import_job.rows_failed = 2
        assert import_job.success_rate == 80.0

    def test_status_choices(self):
        assert ImportJob.Status.PENDING == "pending"
        assert ImportJob.Status.COMPLETED == "completed"
        assert ImportJob.Status.FAILED == "failed"


# ── Integration: Pipeline with CSV ──


@pytest.mark.django_db
class TestImportPipeline:
    def test_csv_import_creates_tours(self, import_job, tmp_path):
        csv_content = (
            "tour_name,price,duration_days,destination,category\n"
            "Japan Spring,29900,5,Japan,Cultural\n"
            "Korea Autumn,19900,3,Korea,Adventure\n"
        )
        csv_file = tmp_path / "tours.csv"
        csv_file.write_text(csv_content)

        import_job.file_format = ImportJob.FileFormat.CSV
        import_job.uploaded_file.name = str(csv_file)
        import_job.save()

        # Patch parse to use our file directly
        pipeline = ImportPipeline(import_job)
        from apps.importer.parsers.csv_parser import CsvParser

        parser = CsvParser()
        parse_result = parser.parse_file(str(csv_file))

        mapping = pipeline.mapper.get_effective_mapping(parse_result.headers)
        assert "tour_name" in mapping
        assert mapping["tour_name"] == "title"

        # Process rows
        import_job.status = ImportJob.Status.IMPORTING
        import_job.save()

        for row_num, row_data in enumerate(parse_result.rows, start=1):
            pipeline._process_row(row_num, row_data, mapping)

        assert pipeline.stats["created"] == 2
        assert Tour.objects.filter(title="Japan Spring").exists()
        assert Tour.objects.filter(title="Korea Autumn").exists()

    def test_skips_rows_without_title(self, import_job):
        pipeline = ImportPipeline(import_job)
        mapping = {"col": "description"}
        pipeline._process_row(1, {"col": "just a description"}, mapping)
        assert pipeline.stats["skipped"] == 1

    def test_upsert_updates_existing(self, import_job, tour):
        pipeline = ImportPipeline(import_job)
        mapping = {"name": "title", "code": "product_code", "desc": "description"}
        row = {"name": "Updated Title", "code": tour.product_code, "desc": "New desc"}
        mapped = pipeline.mapper.map_row(row, mapping)

        tour_obj, action = pipeline._upsert_tour(mapped, row)
        assert action == "updated"
        tour_obj.refresh_from_db()
        assert tour_obj.description == "New desc"
