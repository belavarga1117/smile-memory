"""Debug command: print raw Zego API response for PDF-related fields.

Usage:
    python manage.py debug_zego --sample=5
    python manage.py debug_zego --sample=10 --show-all-fields

Requires ZEGO_USERNAME and ZEGO_PASSWORD in environment (or .env).
"""

import os

from django.core.management.base import BaseCommand, CommandError

from apps.importer.scrapers.zego import ZegoScraper


class Command(BaseCommand):
    help = "Debug Zego API: print raw PDF/Word fields for sample tours"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sample",
            type=int,
            default=10,
            help="Number of tours to inspect (default: 10)",
        )
        parser.add_argument(
            "--show-all-fields",
            action="store_true",
            help="Print all fields from first tour (for full API inspection)",
        )
        parser.add_argument(
            "--country",
            help="Filter by country code (e.g. Japan, Turkey)",
        )

    def handle(self, *args, **options):
        username = os.environ.get("ZEGO_USERNAME", "")
        password = os.environ.get("ZEGO_PASSWORD", "")

        if not username or not password:
            raise CommandError(
                "ZEGO_USERNAME and ZEGO_PASSWORD must be set in .env or environment."
            )

        self.stdout.write(f"Logging in to Zego as {username}...")

        scraper = ZegoScraper(username=username, password=password)
        scraper._login()

        self.stdout.write("Fetching tour listing...")
        raw_data = scraper._fetch_tour_listing()
        self.stdout.write(f"Total rows from API: {len(raw_data)}")

        # Group by programtour_id (same as discover_tours)
        programs = {}
        for row in raw_data:
            pid = row.get("programtour_id", "")
            if not pid:
                continue
            if options["country"]:
                if options["country"].lower() not in row.get("Country_EN", "").lower():
                    continue
            if pid not in programs:
                programs[pid] = row  # keep first row per program

        self.stdout.write(f"Unique programs: {len(programs)}")
        self.stdout.write("-" * 70)

        # Show all fields from first tour if requested
        if options["show_all_fields"] and programs:
            first = next(iter(programs.values()))
            self.stdout.write("\n=== ALL FIELDS IN FIRST TOUR ROW ===")
            for key, val in sorted(first.items()):
                self.stdout.write(f"  {key}: {repr(val)[:100]}")
            self.stdout.write("=" * 70)

        # Sample PDF/Word fields
        sample_n = options["sample"]
        self.stdout.write(f"\n=== PDF/WORD FIELDS FOR FIRST {sample_n} PROGRAMS ===")

        has_pdf = 0
        has_word = 0
        no_file = 0

        for i, (pid, row) in enumerate(list(programs.items())[:sample_n]):
            code = row.get("programtour_code", "?")
            name = row.get("programtour_name", "?")[:40]
            upload_pdf = row.get("upload_pdf", "")
            upload_word = row.get("upload_word", "")
            country = row.get("Country_EN", "?")

            # Build URL if file exists
            base = scraper.base_url
            pdf_url = (
                f"{base}/uploadfile/p_d_f/programtour/{upload_pdf}"
                if upload_pdf
                else ""
            )
            word_url = (
                f"{base}/uploadfile/word/programtour/{upload_word}"
                if upload_word
                else ""
            )

            status = (
                "✅ PDF" if upload_pdf else ("📝 WORD" if upload_word else "❌ NO FILE")
            )
            self.stdout.write(f"\n[{i + 1}] {code} | {country} | {name}")
            self.stdout.write(f"     upload_pdf:  {repr(upload_pdf)}")
            self.stdout.write(f"     upload_word: {repr(upload_word)}")
            if pdf_url:
                self.stdout.write(f"     → PDF URL:  {pdf_url}")
            if word_url:
                self.stdout.write(f"     → WORD URL: {word_url}")
            self.stdout.write(f"     Status: {status}")

            if upload_pdf:
                has_pdf += 1
            elif upload_word:
                has_word += 1
            else:
                no_file += 1

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"SUMMARY (first {sample_n} programs):")
        self.stdout.write(f"  Has PDF:      {has_pdf}")
        self.stdout.write(f"  Has Word doc: {has_word}")
        self.stdout.write(f"  No file:      {no_file}")

        if has_pdf == 0 and has_word == 0:
            self.stdout.write(
                "\n⚠️  No PDF or Word files found. Zego may not upload tour documents "
                "to this portal, or the file fields use a different API field name."
            )
            self.stdout.write(
                "Run with --show-all-fields to inspect all available API fields."
            )
