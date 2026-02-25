"""Management command to scrape tour data from wholesaler websites.

Usage:
    # Scrape all Go365 tours (all countries)
    python manage.py scrape_tours --source=go365

    # Single country only
    python manage.py scrape_tours --source=go365 --country=Japan

    # Single URL
    python manage.py scrape_tours --source=go365 --url=https://www.go365travel.com/tour/China/11482-1093438-38

    # Dry run (parse but don't save to DB)
    python manage.py scrape_tours --source=go365 --dry-run

    # Verbose output
    python manage.py scrape_tours --source=go365 --country=Japan -v2
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.importer.models import ImportJob, ImportLog
from apps.importer.scrapers import get_scraper
from apps.tours.models import (
    Airline,
    Destination,
    ItineraryDay,
    Tour,
    TourDeparture,
    TourImage,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape tour data from wholesaler websites (Go365, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            help="Scraper source name: go365",
        )
        parser.add_argument(
            "--country",
            help="Scrape only this country (e.g. Japan, China)",
        )
        parser.add_argument(
            "--url",
            help="Scrape a single tour URL instead of discovering",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Parse tours but don't save to database",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Auto-publish scraped tours (default: draft)",
        )
        parser.add_argument(
            "--zego-user",
            help="Zego portal username (or set ZEGO_USERNAME env var)",
        )
        parser.add_argument(
            "--zego-pass",
            help="Zego portal password (or set ZEGO_PASSWORD env var)",
        )
        parser.add_argument(
            "--gs25-user",
            help="GS25 portal username (or set GS25_USERNAME env var)",
        )
        parser.add_argument(
            "--gs25-pass",
            help="GS25 portal password (or set GS25_PASSWORD env var)",
        )

    def handle(self, *args, **options):
        source = options["source"]
        country = options.get("country")
        single_url = options.get("url")
        dry_run = options["dry_run"]
        publish = options["publish"]
        verbosity = options["verbosity"]

        if verbosity >= 2:
            logging.basicConfig(level=logging.DEBUG)
        elif verbosity >= 1:
            logging.basicConfig(level=logging.INFO)

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"  Tour Scraper — source: {source}")
        if country:
            self.stdout.write(f"  Country filter: {country}")
        if single_url:
            self.stdout.write(f"  Single URL: {single_url}")
        if dry_run:
            self.stdout.write("  Mode: DRY RUN (no DB writes)")
        self.stdout.write(f"{'=' * 60}\n")

        # Build scraper kwargs
        scraper_kwargs = {}
        if source.lower() == "zego":
            import os

            scraper_kwargs["username"] = options.get("zego_user") or os.environ.get(
                "ZEGO_USERNAME", ""
            )
            scraper_kwargs["password"] = options.get("zego_pass") or os.environ.get(
                "ZEGO_PASSWORD", ""
            )
        elif source.lower() == "gs25":
            import os

            scraper_kwargs["username"] = options.get("gs25_user") or os.environ.get(
                "GS25_USERNAME", ""
            )
            scraper_kwargs["password"] = options.get("gs25_pass") or os.environ.get(
                "GS25_PASSWORD", ""
            )

        # Get scraper
        try:
            scraper = get_scraper(source, **scraper_kwargs)
        except ValueError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        # Mark any previously stuck jobs for this source as failed
        if not dry_run:
            stuck_statuses = [
                ImportJob.Status.IMPORTING,
                ImportJob.Status.PARSING,
                ImportJob.Status.MAPPING,
            ]
            ImportJob.objects.filter(
                source=source.lower(), status__in=stuck_statuses
            ).update(
                status=ImportJob.Status.FAILED,
                error_message="Interrupted — process was killed before completion (e.g. container restart).",
            )

        # Create ImportJob for tracking (unless dry run)
        job = None
        if not dry_run:
            job = ImportJob.objects.create(
                name=f"Scrape {source}" + (f" — {country}" if country else ""),
                source=source.lower(),
                file_format="html",
                source_url=single_url or scraper.base_url,
                status=ImportJob.Status.IMPORTING,
                started_at=timezone.now(),
            )

        # Discover or use single URL
        if single_url:
            tour_list = [{"url": single_url, "external_id": "", "title": ""}]
            self.stdout.write(f"Scraping single URL: {single_url}\n")
        else:
            self.stdout.write("Discovering tour URLs...\n")
            tour_list = scraper.discover_tours(country=country)
            self.stdout.write(
                self.style.SUCCESS(f"Found {len(tour_list)} tours to scrape\n")
            )

        if not tour_list:
            self.stdout.write(self.style.WARNING("No tours found. Exiting."))
            if job:
                job.status = ImportJob.Status.COMPLETED
                job.completed_at = timezone.now()
                job.save()
            return

        # Scrape each tour
        stats = {"created": 0, "updated": 0, "failed": 0, "skipped": 0}
        total = len(tour_list)

        for i, tour_info in enumerate(tour_list, 1):
            url = tour_info.get("url", "")
            label = tour_info.get("title", url)[:80] or url
            self.stdout.write(f"[{i}/{total}] {label}")

            try:
                # API-based scrapers: data pre-fetched in discover_tours
                if (
                    "_raw_rows" in tour_info or "_raw_product" in tour_info
                ) and hasattr(scraper, "scrape_program"):
                    data = scraper.scrape_program(tour_info)
                else:
                    data = scraper.scrape_tour(url)

                if not data:
                    self.stdout.write(self.style.WARNING("  → No data parsed"))
                    stats["skipped"] += 1
                    self._log(job, i, "warning", f"No data parsed: {url}")
                    continue

                if dry_run:
                    self._print_tour_data(data)
                    stats["created"] += 1
                else:
                    tour, action = self._upsert_tour(data, publish=publish)
                    stats[action] += 1
                    self._log(
                        job,
                        i,
                        "success",
                        f"{action.title()}: {tour.title[:60]}",
                        raw_data={
                            "url": url,
                            "product_code": data.get("product_code", ""),
                        },
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  → {action}: {data.get('title', '?')[:60]}"
                        )
                    )

            except Exception as e:
                stats["failed"] += 1
                self._log(job, i, "error", f"Error: {e}", raw_data={"url": url})
                self.stderr.write(self.style.ERROR(f"  → Error: {e}"))

        # Summary
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("  Summary:")
        self.stdout.write(f"    Created: {stats['created']}")
        self.stdout.write(f"    Updated: {stats['updated']}")
        self.stdout.write(f"    Skipped: {stats['skipped']}")
        self.stdout.write(f"    Failed:  {stats['failed']}")
        self.stdout.write(f"{'=' * 60}\n")

        # Finalize ImportJob
        if job:
            job.total_rows = total
            job.rows_created = stats["created"]
            job.rows_updated = stats["updated"]
            job.rows_skipped = stats["skipped"]
            job.rows_failed = stats["failed"]
            job.completed_at = timezone.now()
            if stats["failed"] > 0 and (stats["created"] + stats["updated"]) > 0:
                job.status = ImportJob.Status.PARTIAL
            elif stats["failed"] > 0:
                job.status = ImportJob.Status.FAILED
            else:
                job.status = ImportJob.Status.COMPLETED
            job.save()

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN — no data was saved to the database.")
            )

    def _upsert_tour(self, data, publish=False):
        """Create or update a Tour from scraped data."""
        # Pop related data
        itinerary = data.pop("_itinerary", [])
        departures = data.pop("_departures", [])
        images = data.pop("_images", [])
        data.pop("_flights", [])  # Flights stored at departure level, not used here

        # Pop Zego-specific fields that need special handling
        locations = data.pop("locations", None)
        total_meals = data.pop("total_meals", None)
        plane_meals = data.pop("plane_meals", None)
        word_url = data.pop("word_url", None)

        # Resolve destination
        destination = None
        dest_name = data.pop("destination_name", "")
        if dest_name:
            destination, _ = Destination.objects.get_or_create(
                slug=slugify(dest_name),
                defaults={"name": dest_name},
            )

        # Resolve airline
        airline = None
        airline_code = data.pop("airline_code", "")
        if airline_code:
            airline = Airline.objects.filter(code=airline_code).first()
            if not airline:
                airline = Airline.objects.create(
                    code=airline_code,
                    name=airline_code,  # Will be updated manually
                )

        # Lookup existing tour by product_code
        tour = None
        action = "created"
        product_code = data.get("product_code")

        if product_code:
            tour = Tour.objects.filter(product_code=product_code).first()

        # Fallback: lookup by source + external_id
        source = data.get("source", "")
        if not tour and data.get("external_id") and source:
            tour = Tour.objects.filter(
                source=source, external_id=data["external_id"]
            ).first()

        with transaction.atomic():
            if tour:
                action = "updated"
                # Update fields (don't overwrite non-empty with empty)
                for field in [
                    "title",
                    "title_th",
                    "duration_days",
                    "duration_nights",
                    "price_from",
                    "includes",
                    "includes_th",
                    "excludes",
                    "excludes_th",
                    "hero_image_url",
                    "source_url",
                    "highlight",
                    "highlight_th",
                    "hotel_stars_min",
                    "hotel_stars_max",
                    "pdf_url",
                ]:
                    new_val = data.get(field)
                    if new_val is not None and new_val != "":
                        setattr(tour, field, new_val)
                # Zego-specific fields
                if locations is not None:
                    tour.locations = locations
                if total_meals is not None:
                    tour.total_meals = total_meals
                if plane_meals is not None:
                    tour.plane_meals = plane_meals
                if word_url:
                    tour.word_url = word_url
                tour.source = source
                tour.external_id = data.get("external_id", tour.external_id)
                tour.last_synced_at = timezone.now()
                tour.save()
            else:
                # Generate unique slug
                base_slug = slugify(data.get("title", "tour"))[:200] or f"{source}-tour"
                slug = base_slug
                counter = 1
                while Tour.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                create_kwargs = dict(
                    title=data.get("title", ""),
                    title_th=data.get("title_th", ""),
                    slug=slug,
                    product_code=product_code or None,
                    duration_days=data.get("duration_days"),
                    duration_nights=data.get("duration_nights"),
                    price_from=data.get("price_from"),
                    includes=data.get("includes", ""),
                    includes_th=data.get("includes_th", ""),
                    excludes=data.get("excludes", ""),
                    excludes_th=data.get("excludes_th", ""),
                    highlight=data.get("highlight", ""),
                    highlight_th=data.get("highlight_th", ""),
                    hotel_stars_min=data.get("hotel_stars_min"),
                    hotel_stars_max=data.get("hotel_stars_max"),
                    hero_image_url=data.get("hero_image_url", ""),
                    pdf_url=data.get("pdf_url", ""),
                    source=source,
                    source_url=data.get("source_url", ""),
                    external_id=data.get("external_id", ""),
                    last_synced_at=timezone.now(),
                    status=Tour.Status.PUBLISHED
                    if (publish and data.get("pdf_url"))
                    else Tour.Status.DRAFT,
                )
                # Zego-specific fields
                if locations is not None:
                    create_kwargs["locations"] = locations
                if total_meals is not None:
                    create_kwargs["total_meals"] = total_meals
                if plane_meals is not None:
                    create_kwargs["plane_meals"] = plane_meals
                if word_url:
                    create_kwargs["word_url"] = word_url
                tour = Tour.objects.create(**create_kwargs)

            # Link airline
            if airline:
                tour.airline = airline
                tour.save(update_fields=["airline"])

            # Link destination (M2M)
            if destination:
                tour.destinations.add(destination)

            # Upsert itinerary days
            if itinerary:
                self._upsert_itinerary(tour, itinerary)

            # Upsert departures
            if departures:
                self._upsert_departures(tour, departures)

            # Upsert images
            if images:
                self._upsert_images(tour, images)

            # Update price_from from departures
            tour.update_price_from()

        return tour, action

    def _upsert_itinerary(self, tour, itinerary):
        """Create/update ItineraryDay records."""
        for day_data in itinerary:
            day_num = day_data["day_number"]
            meals = day_data.get("meals", {})

            defaults = {
                "title": day_data.get("title", f"Day {day_num}")[:300],
                "title_th": day_data.get("title", f"วันที่ {day_num}")[:300],
                "description": day_data.get("description", ""),
                "description_th": day_data.get("description", ""),
                "breakfast": meals.get("breakfast", "N"),
                "lunch": meals.get("lunch", "N"),
                "dinner": meals.get("dinner", "N"),
                "hotel_name": day_data.get("hotel", "")[:300],
            }
            # Meal descriptions (from Zego)
            for meal_field in [
                "breakfast_description",
                "lunch_description",
                "dinner_description",
            ]:
                val = day_data.get(meal_field, "")
                if val:
                    defaults[meal_field] = val[:300]

            ItineraryDay.objects.update_or_create(
                tour=tour,
                day_number=day_num,
                defaults=defaults,
            )

    def _upsert_departures(self, tour, departures):
        """Create/update TourDeparture records."""
        for dep_data in departures:
            dep_date = dep_data.get("departure_date")
            ret_date = dep_data.get("return_date")
            price = dep_data.get("price_adult")

            if not dep_date:
                continue

            # price_adult is required — skip departures without it
            if not price:
                logger.warning("Skipping departure %s: no price_adult", dep_date)
                continue

            if not ret_date and tour.duration_days:
                ret_date = dep_date + timedelta(days=tour.duration_days - 1)
            elif not ret_date:
                ret_date = dep_date

            # Map status
            status_map = {
                "available": TourDeparture.PeriodStatus.AVAILABLE,
                "soldout": TourDeparture.PeriodStatus.SOLDOUT,
                "waitlist": TourDeparture.PeriodStatus.WAITLIST,
                "closed": TourDeparture.PeriodStatus.CLOSED,
            }
            status = status_map.get(
                dep_data.get("status", "available"),
                TourDeparture.PeriodStatus.AVAILABLE,
            )

            defaults = {
                "return_date": ret_date,
                "status": status,
                "period_code": dep_data.get("period_code", ""),
            }
            if price:
                defaults["price_adult"] = price
            # Optional pricing fields
            for field in [
                "price_child",
                "price_child_no_bed",
                "price_single_supplement",
                # Zego-specific
                "price_join_land",
                "deposit",
                "price_adult_promo",
                "price_child_promo",
                "price_single_visa",
                "group_size",
                "booked",
                "bus",
            ]:
                val = dep_data.get(field)
                if val is not None and val != "":
                    defaults[field] = val

            try:
                TourDeparture.objects.update_or_create(
                    tour=tour,
                    departure_date=dep_date,
                    defaults=defaults,
                )
            except Exception as e:
                logger.warning("Failed to create departure %s: %s", dep_date, e)

    def _upsert_images(self, tour, image_urls):
        """Create TourImage records for new images."""
        existing = set(tour.images.values_list("image_url", flat=True))

        for i, url in enumerate(image_urls):
            if url not in existing:
                TourImage.objects.create(
                    tour=tour,
                    image_url=url,
                    sort_order=i,
                )

    def _print_tour_data(self, data):
        """Pretty-print tour data for dry run."""
        self.stdout.write(self.style.SUCCESS(f"  Title: {data.get('title', '?')[:80]}"))
        self.stdout.write(f"  Code: {data.get('product_code', '-')}")
        self.stdout.write(
            f"  Duration: {data.get('duration_days', '?')}D/{data.get('duration_nights', '?')}N"
        )
        self.stdout.write(f"  Price: {data.get('price_from', '-')} THB")
        self.stdout.write(f"  Airline: {data.get('airline_code', '-')}")
        self.stdout.write(f"  Destination: {data.get('destination_name', '-')}")

        itin = data.get("_itinerary", [])
        self.stdout.write(f"  Itinerary: {len(itin)} days")

        deps = data.get("_departures", [])
        self.stdout.write(f"  Departures: {len(deps)} dates")

        imgs = data.get("_images", [])
        self.stdout.write(f"  Images: {len(imgs)}")

        flights = data.get("_flights", [])
        if flights:
            self.stdout.write(f"  Flights: {len(flights)}")
        self.stdout.write("")

    def _log(self, job, row_num, level, message, raw_data=None):
        """Create ImportLog entry if job exists."""
        if job:
            ImportLog.objects.create(
                job=job,
                row_number=row_num,
                level=level,
                message=message,
                raw_data=raw_data or {},
            )
