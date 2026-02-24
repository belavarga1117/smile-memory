"""Import pipeline orchestrator — coordinates parsing, mapping, and upserting tours."""

import logging

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.tours.models import Airline, Category, Destination, Tour, TourDeparture

from .mappers import TourMapper
from .models import ImportJob, ImportLog
from .parsers import get_parser

logger = logging.getLogger(__name__)


class ImportPipeline:
    """Orchestrates the full import flow:

    1. Parse file → structured rows
    2. Map fields → Tour-compatible dicts
    3. Validate → skip bad rows
    4. Upsert → create or update Tours (+ departures)
    5. Log → per-row results
    """

    def __init__(self, job: ImportJob):
        self.job = job
        self.mapper = TourMapper(field_mapping=job.field_mapping or {})
        self.stats = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}

    def run(self):
        """Execute the full import pipeline."""
        self.job.status = ImportJob.Status.PARSING
        self.job.started_at = timezone.now()
        self.job.save(update_fields=["status", "started_at"])

        try:
            # Step 1: Parse
            parse_result = self._parse()
            if parse_result.errors and not parse_result.rows:
                self._fail("; ".join(parse_result.errors))
                return self.job

            self.job.total_rows = parse_result.total_rows
            self.job.parsed_headers = parse_result.headers
            self.job.parsed_preview = parse_result.rows[:10]
            self.job.save(
                update_fields=["total_rows", "parsed_headers", "parsed_preview"]
            )

            # Step 2: Map fields
            self.job.status = ImportJob.Status.MAPPING
            self.job.save(update_fields=["status"])

            mapping = self.mapper.get_effective_mapping(parse_result.headers)
            if not mapping:
                self._fail(
                    "No field mapping could be determined. Please configure mapping manually."
                )
                return self.job

            # Save auto-detected mapping back to job for reference
            if not self.job.field_mapping:
                self.job.field_mapping = mapping
                self.job.save(update_fields=["field_mapping"])

            # Step 3: Import rows
            self.job.status = ImportJob.Status.IMPORTING
            self.job.save(update_fields=["status"])

            for row_num, row_data in enumerate(parse_result.rows, start=1):
                self._process_row(row_num, row_data, mapping)

            # Step 4: Finalize
            self.job.rows_created = self.stats["created"]
            self.job.rows_updated = self.stats["updated"]
            self.job.rows_skipped = self.stats["skipped"]
            self.job.rows_failed = self.stats["failed"]
            self.job.completed_at = timezone.now()

            if (
                self.stats["failed"] > 0
                and (self.stats["created"] + self.stats["updated"]) > 0
            ):
                self.job.status = ImportJob.Status.PARTIAL
            elif self.stats["failed"] > 0:
                self.job.status = ImportJob.Status.FAILED
            else:
                self.job.status = ImportJob.Status.COMPLETED

            self.job.save()
            logger.info(
                "Import %s finished: %d created, %d updated, %d skipped, %d failed",
                self.job.pk,
                self.stats["created"],
                self.stats["updated"],
                self.stats["skipped"],
                self.stats["failed"],
            )

        except Exception as e:
            logger.exception("Import pipeline failed: %s", e)
            self._fail(str(e))

        return self.job

    def preview_only(self):
        """Parse and return preview data without importing."""
        self.job.status = ImportJob.Status.PARSING
        self.job.save(update_fields=["status"])

        parse_result = self._parse()
        if parse_result.errors and not parse_result.rows:
            self._fail("; ".join(parse_result.errors))
            return self.job

        mapping = self.mapper.get_effective_mapping(parse_result.headers)

        self.job.total_rows = parse_result.total_rows
        self.job.parsed_headers = parse_result.headers
        self.job.parsed_preview = parse_result.rows[:20]
        self.job.field_mapping = mapping
        self.job.status = ImportJob.Status.PENDING  # Back to pending, awaiting confirm
        self.job.save()

        return self.job

    def _parse(self):
        """Parse the uploaded file or URL."""
        parser = get_parser(self.job.file_format)

        if self.job.file_format == "html" and self.job.source_url:
            return parser.parse_url(self.job.source_url)
        elif self.job.uploaded_file:
            return parser.parse_file(self.job.uploaded_file.path)
        else:
            from .parsers.base import ParseResult

            return ParseResult(errors=["No file or URL provided."])

    def _process_row(self, row_num, row_data, mapping):
        """Map, validate, and upsert a single row."""
        try:
            mapped = self.mapper.map_row(row_data, mapping)

            # Validate: must have title or product_code
            if not mapped.get("title") and not mapped.get("product_code"):
                self._log(
                    row_num, "warning", "Skipped: no title or product code", row_data
                )
                self.stats["skipped"] += 1
                return

            # Upsert tour
            with transaction.atomic():
                tour, action = self._upsert_tour(mapped, row_data)

            if action == "created":
                self.stats["created"] += 1
                self._log(row_num, "success", f"Created: {tour.title}", row_data)
            else:
                self.stats["updated"] += 1
                self._log(row_num, "success", f"Updated: {tour.title}", row_data)

        except Exception as e:
            self.stats["failed"] += 1
            self._log(row_num, "error", f"Error: {e}", row_data)
            logger.warning("Row %d failed: %s", row_num, e)

    def _upsert_tour(self, mapped, raw_data):
        """Create or update a Tour from mapped data.

        Lookup strategy:
        1. product_code (unique identifier from wholesaler)
        2. slug match
        3. Create new
        """
        # Resolve related objects
        destination = self._resolve_destination(mapped.pop("destination_name", None))
        category = self._resolve_category(mapped.pop("category_name", None))
        airline = self._resolve_airline(mapped.pop("airline_code", None))

        # Departure data (extracted before Tour upsert)
        departure_date = mapped.pop("departure_date", None)
        return_date = mapped.pop("return_date", None)
        price_child = mapped.pop("price_child", None)

        # Lookup existing tour
        tour = None
        action = "created"

        product_code = mapped.get("product_code")
        if product_code:
            tour = Tour.objects.filter(product_code=product_code).first()

        if not tour and mapped.get("slug"):
            tour = Tour.objects.filter(slug=mapped["slug"]).first()

        if tour:
            action = "updated"
            # Update fields (don't overwrite non-empty with empty)
            for field, value in mapped.items():
                if field in ("slug",) and getattr(tour, field):
                    continue  # Don't overwrite existing slug
                if value is not None and value != "":
                    setattr(tour, field, value)
        else:
            # Ensure unique slug
            mapped["slug"] = self._unique_slug(mapped.get("slug", "imported-tour"))
            tour = Tour(
                **{k: v for k, v in mapped.items() if v is not None and v != ""}
            )

        # Set source info
        tour.source = tour.source or self.job.get_source_display()
        tour.last_synced_at = timezone.now()

        if airline:
            tour.airline = airline

        tour.save()

        # Link M2M
        if destination:
            tour.destinations.add(destination)
        if category:
            tour.categories.add(category)

        # Create departure if date provided
        if departure_date:
            self._upsert_departure(
                tour, departure_date, return_date, mapped, price_child
            )

        return tour, action

    def _upsert_departure(self, tour, departure_date, return_date, mapped, price_child):
        """Create or update a TourDeparture."""
        price_from = mapped.get("price_from")
        if not price_from:
            return

        if not return_date and tour.duration_days:
            from datetime import timedelta

            return_date = departure_date + timedelta(days=tour.duration_days - 1)
        elif not return_date:
            return_date = departure_date

        dep, created = TourDeparture.objects.update_or_create(
            tour=tour,
            departure_date=departure_date,
            defaults={
                "return_date": return_date,
                "price_adult": price_from,
                "price_child": price_child,
                "status": TourDeparture.PeriodStatus.AVAILABLE,
            },
        )
        # Update tour's price_from
        tour.update_price_from()

    def _resolve_destination(self, name):
        """Find or create a Destination by name."""
        if not name:
            return None
        name = str(name).strip()
        dest, _ = Destination.objects.get_or_create(
            slug=slugify(name),
            defaults={"name": name},
        )
        return dest

    def _resolve_category(self, name):
        """Find or create a Category by name."""
        if not name:
            return None
        name = str(name).strip()
        cat, _ = Category.objects.get_or_create(
            slug=slugify(name),
            defaults={"name": name},
        )
        return cat

    def _resolve_airline(self, code):
        """Find an Airline by IATA code."""
        if not code:
            return None
        code = str(code).strip().upper()
        return Airline.objects.filter(code=code).first()

    def _unique_slug(self, base_slug):
        """Generate a unique slug by appending a number if needed."""
        slug = base_slug
        counter = 1
        while Tour.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def _log(self, row_number, level, message, raw_data=None):
        """Create an ImportLog entry."""
        ImportLog.objects.create(
            job=self.job,
            row_number=row_number,
            level=level,
            message=message,
            raw_data=raw_data or {},
        )

    def _fail(self, error_message):
        """Mark the job as failed."""
        self.job.status = ImportJob.Status.FAILED
        self.job.error_message = error_message
        self.job.completed_at = timezone.now()
        self.job.save()
        logger.error("Import %s failed: %s", self.job.pk, error_message)
