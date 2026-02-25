"""Clean raw HTML from Zego tour fields that were imported before HTML stripping was added.

Cleans:
- Tour.highlight / highlight_th (Zego portal junk modal text)
- ItineraryDay.description / description_th (raw HTML tags/classes)

Usage:
    python manage.py clean_tour_html
    python manage.py clean_tour_html --dry-run
    python manage.py clean_tour_html --source=zego   # only Zego tours
"""

from django.core.management.base import BaseCommand

from apps.importer.scrapers.zego import ZegoScraper
from apps.tours.models import ItineraryDay, Tour


class Command(BaseCommand):
    help = (
        "Strip raw HTML/junk from Zego tour highlight and itinerary description fields"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving",
        )
        parser.add_argument(
            "--source",
            default="zego",
            help="Only clean tours from this source (default: zego)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        source = options["source"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — not saving\n"))

        # We use ZegoScraper._html_to_text() without authenticating
        scraper = ZegoScraper()

        self._clean_highlights(scraper, source, dry_run)
        self._clean_itinerary_descriptions(scraper, source, dry_run)

    def _clean_highlights(self, scraper, source, dry_run):
        tours = Tour.objects.filter(source=source).exclude(highlight="")
        self.stdout.write(f"\nCleaning highlight for {tours.count()} {source} tours...")

        updated = 0
        for tour in tours:
            changed = False
            new_highlight = (
                scraper._html_to_text(tour.highlight) if tour.highlight else ""
            )
            new_highlight_th = (
                scraper._html_to_text(tour.highlight_th) if tour.highlight_th else ""
            )

            if new_highlight != tour.highlight or new_highlight_th != tour.highlight_th:
                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {tour.product_code}: highlight changed\n"
                        f"    WAS: {repr(tour.highlight[:80])}\n"
                        f"    NOW: {repr(new_highlight[:80])}"
                    )
                else:
                    tour.highlight = new_highlight
                    tour.highlight_th = new_highlight_th
                    tour.save(update_fields=["highlight", "highlight_th"])
                updated += 1
                changed = True

            if not changed and not dry_run:
                pass  # already clean

        self.stdout.write(self.style.SUCCESS(f"  {updated} tour highlights cleaned"))

    def _clean_itinerary_descriptions(self, scraper, source, dry_run):
        days = ItineraryDay.objects.filter(tour__source=source).exclude(description="")
        self.stdout.write(
            f"\nCleaning itinerary descriptions for {days.count()} {source} days..."
        )

        updated = 0
        for day in days:
            new_desc = scraper._html_to_text(day.description) if day.description else ""
            new_desc_th = (
                scraper._html_to_text(day.description_th) if day.description_th else ""
            )

            if new_desc != day.description or new_desc_th != day.description_th:
                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {day.tour.product_code} Day {day.day_number}: desc changed\n"
                        f"    WAS: {repr(day.description[:80])}\n"
                        f"    NOW: {repr(new_desc[:80])}"
                    )
                else:
                    day.description = new_desc
                    day.description_th = new_desc_th
                    day.save(update_fields=["description", "description_th"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"  {updated} itinerary days descriptions cleaned")
        )
