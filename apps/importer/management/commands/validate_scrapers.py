"""Management command to validate scraped data against live wholesaler sources.

Picks a sample of tours from the DB for each source, re-fetches them live,
and compares key fields to detect drift or scraper regressions.

Usage:
    python manage.py validate_scrapers
    python manage.py validate_scrapers --source=zego
    python manage.py validate_scrapers --sample=10
"""

import os
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.importer.scrapers import get_scraper
from apps.tours.models import Tour, TourDeparture


SOURCES = ["zego", "go365", "realjourney", "gs25"]

# How many tours to sample per source
DEFAULT_SAMPLE = 5

# Price tolerance: live vs DB may differ by up to this fraction (e.g. 0.15 = 15%)
PRICE_TOLERANCE = 0.15


class Command(BaseCommand):
    help = "Validate scraped tour data against live wholesaler sources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=SOURCES,
            help="Validate only this source (default: all)",
        )
        parser.add_argument(
            "--sample",
            type=int,
            default=DEFAULT_SAMPLE,
            help=f"Tours to sample per source (default: {DEFAULT_SAMPLE})",
        )

    def handle(self, *args, **options):
        sources = [options["source"]] if options["source"] else SOURCES
        sample_size = options["sample"]

        self.out("\n" + "=" * 70)
        self.out("  Scraper Data Validation")
        self.out("=" * 70)

        overall_ok = 0
        overall_warn = 0
        overall_fail = 0

        for source in sources:
            ok, warn, fail = self._validate_source(source, sample_size)
            overall_ok += ok
            overall_warn += warn
            overall_fail += fail

        self.out("\n" + "=" * 70)
        self.out("  OVERALL RESULTS")
        self.out(f"  OK:      {overall_ok}")
        self.out(f"  WARN:    {overall_warn}")
        self.out(f"  FAIL:    {overall_fail}")
        self.out("=" * 70 + "\n")

    # ------------------------------------------------------------------ #
    #  Per-source validation
    # ------------------------------------------------------------------ #

    def _validate_source(self, source: str, sample_size: int) -> tuple[int, int, int]:
        self.out(f"\n{'─' * 70}")
        self.out(f"  Source: {source.upper()}")
        self.out("─" * 70)

        # Pick random DB tours for this source
        db_tours = list(Tour.objects.filter(source=source).order_by("?")[:sample_size])
        if not db_tours:
            self.warn(f"  No DB tours found for source={source}. Skipping.")
            return 0, 1, 0

        self.out(f"  Sampled {len(db_tours)} tours from DB")

        # Build scraper
        try:
            scraper = self._build_scraper(source)
        except Exception as e:
            self.fail(f"  Could not build scraper for {source}: {e}")
            return 0, 0, len(db_tours)

        # Fetch live data and compare
        ok = warn = fail = 0
        try:
            if source == "gs25":
                ok, warn, fail = self._validate_gs25(scraper, db_tours)
            else:
                ok, warn, fail = self._validate_api_source(scraper, source, db_tours)
        except Exception as e:
            self.fail(f"  Validation error for {source}: {e}")
            fail += len(db_tours)

        self.out(f"\n  Source summary — OK: {ok}  WARN: {warn}  FAIL: {fail}")
        return ok, warn, fail

    def _validate_api_source(
        self, scraper, source: str, db_tours: list
    ) -> tuple[int, int, int]:
        """Validate API-based sources (Zego, Go365, RealJourney).

        These load all tours in one call; we match by external_id.
        """
        self.out("  Fetching live tour list...")
        try:
            live_list = scraper.discover_tours()
        except Exception as e:
            self.fail(f"  discover_tours() failed: {e}")
            return 0, 0, len(db_tours)

        self.out(f"  Live source has {len(live_list)} tours")

        # Build index: external_id → tour_info
        live_index = {str(t.get("external_id", "")): t for t in live_list}

        ok = warn = fail = 0
        for db_tour in db_tours:
            tour_info = live_index.get(str(db_tour.external_id))
            if not tour_info:
                self.warn(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    WARN: external_id={db_tour.external_id} not found in live data "
                    f"(may have been removed from wholesaler)"
                )
                warn += 1
                continue

            # Parse live data
            try:
                if hasattr(scraper, "scrape_program"):
                    live_data = scraper.scrape_program(tour_info)
                else:
                    live_data = scraper.scrape_tour(tour_info.get("url", ""))
            except Exception as e:
                self.fail(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    FAIL: scrape_program() error: {e}"
                )
                fail += 1
                continue

            if not live_data:
                self.fail(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    FAIL: scrape_program() returned None"
                )
                fail += 1
                continue

            tour_ok, tour_warn, tour_fail = self._compare(db_tour, live_data)
            ok += tour_ok
            warn += tour_warn
            fail += tour_fail

        return ok, warn, fail

    def _validate_gs25(self, scraper, db_tours: list) -> tuple[int, int, int]:
        """Validate GS25 by re-scraping individual tour detail pages."""
        ok = warn = fail = 0

        for db_tour in db_tours:
            if not db_tour.source_url:
                self.warn(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    WARN: no source_url stored — cannot re-scrape"
                )
                warn += 1
                continue

            try:
                live_data = scraper.scrape_tour(db_tour.source_url)
            except Exception as e:
                self.fail(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    FAIL: scrape_tour() error: {e}"
                )
                fail += 1
                continue

            if not live_data:
                self.warn(
                    f"\n  [{db_tour.product_code}] {db_tour.title[:60]}\n"
                    f"    WARN: scrape_tour() returned None "
                    f"(tour may have been removed from GS25)"
                )
                warn += 1
                continue

            tour_ok, tour_warn, tour_fail = self._compare(db_tour, live_data)
            ok += tour_ok
            warn += tour_warn
            fail += tour_fail

        return ok, warn, fail

    # ------------------------------------------------------------------ #
    #  Field comparison
    # ------------------------------------------------------------------ #

    def _compare(self, db_tour: Tour, live: dict) -> tuple[int, int, int]:
        """Compare DB tour against live scraped data. Returns (ok, warn, fail)."""
        label = f"[{db_tour.product_code or db_tour.external_id}] {db_tour.title[:55]}"
        issues = []

        # 1. Title
        db_title = (db_tour.title or "").strip()
        live_title = (live.get("title") or "").strip()
        if db_title and live_title:
            # Fuzzy: check if first 30 chars roughly match (ignore Thai padding)
            if db_title[:30].lower() != live_title[:30].lower():
                issues.append(
                    f"  title mismatch:\n"
                    f"    DB:   {db_title[:80]}\n"
                    f"    LIVE: {live_title[:80]}"
                )

        # 2. Duration days
        db_days = db_tour.duration_days
        live_days = live.get("duration_days")
        if db_days and live_days and db_days != live_days:
            issues.append(f"  duration_days: DB={db_days}  LIVE={live_days}")

        # 3. Price (within tolerance)
        db_price = db_tour.price_from
        live_price = live.get("price_from")
        if db_price and live_price:
            try:
                lp = Decimal(str(live_price))
                dp = Decimal(str(db_price))
                if dp > 0:
                    diff_pct = abs(lp - dp) / dp
                    if diff_pct > PRICE_TOLERANCE:
                        issues.append(
                            f"  price_from: DB={dp:,.0f}  LIVE={lp:,.0f}  "
                            f"diff={diff_pct:.0%} (>{PRICE_TOLERANCE:.0%} tolerance)"
                        )
            except Exception:
                pass

        # 4. Departure count
        db_dep_count = TourDeparture.objects.filter(tour=db_tour).count()
        live_deps = live.get("_departures", [])
        live_dep_count = len(live_deps)
        if db_dep_count == 0 and live_dep_count > 0:
            issues.append(
                f"  departures: DB has 0 departures but LIVE has {live_dep_count}"
            )
        elif live_dep_count == 0 and db_dep_count > 0:
            issues.append(
                f"  departures: DB has {db_dep_count} but LIVE has 0 "
                f"(tour may be fully booked/expired)"
            )

        # 5. PDF URL presence
        db_has_pdf = bool(db_tour.pdf_url or db_tour.pdf_file)
        live_has_pdf = bool(live.get("pdf_url"))
        if live_has_pdf and not db_has_pdf:
            issues.append("  pdf: LIVE has pdf_url but DB does not — re-sync needed")

        # Output
        if not issues:
            self.ok(f"\n  {label}\n    OK — title, duration, price, departures match")
            return 1, 0, 0
        else:
            severity = "WARN"
            # Any structural mismatch (title, duration) = FAIL; price drift = WARN
            hard_issues = [i for i in issues if "title" in i or "duration" in i]
            if hard_issues:
                severity = "FAIL"

            bullet = "\n    ".join(issues)
            msg = f"\n  {label}\n    {severity}:\n    {bullet}"
            if severity == "FAIL":
                self.fail(msg)
                return 0, 0, 1
            else:
                self.warn(msg)
                return 0, 1, 0

    # ------------------------------------------------------------------ #
    #  Scraper factory
    # ------------------------------------------------------------------ #

    def _build_scraper(self, source: str):
        kwargs = {}
        if source == "zego":
            kwargs["username"] = os.environ.get("ZEGO_USERNAME", "")
            kwargs["password"] = os.environ.get("ZEGO_PASSWORD", "")
        elif source == "gs25":
            kwargs["username"] = os.environ.get("GS25_USERNAME", "")
            kwargs["password"] = os.environ.get("GS25_PASSWORD", "")
        return get_scraper(source, **kwargs)

    # ------------------------------------------------------------------ #
    #  Output helpers
    # ------------------------------------------------------------------ #

    def out(self, msg: str):
        self.stdout.write(msg)

    def ok(self, msg: str):
        self.stdout.write(self.style.SUCCESS(msg))

    def warn(self, msg: str):
        self.stdout.write(self.style.WARNING(msg))

    def fail(self, msg: str):
        self.stdout.write(self.style.ERROR(msg))
