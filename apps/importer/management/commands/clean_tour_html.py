"""Clean raw HTML from tour fields that were imported before HTML stripping was added.

Cleans:
- Tour.highlight / highlight_th (Zego portal junk modal text)
- ItineraryDay.description / description_th (raw HTML tags/classes)
- ItineraryDay.hotel_name (Font Awesome star icons: <i class='fas fa-star'>)
- ItineraryDay.breakfast/lunch/dinner_description (embedded HTML)

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
        "Strip raw HTML/junk from tour text fields (highlights, itinerary, hotel names)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show changes without saving",
        )
        parser.add_argument(
            "--source",
            default="all",
            help="Source to clean: zego, realjourney, go365, or 'all' (default: all)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        source = options["source"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — not saving\n"))

        # ZegoScraper._html_to_text() handles HTML + Zego junk patterns generically
        scraper = ZegoScraper()

        sources = ["zego", "go365", "realjourney"] if source == "all" else [source]
        for src in sources:
            self._clean_highlights(scraper, src, dry_run)
            self._clean_itinerary_descriptions(scraper, src, dry_run)
            self._clean_itinerary_hotel_names(scraper, src, dry_run)
            self._clean_itinerary_meal_descriptions(scraper, src, dry_run)

    def _clean_highlights(self, scraper, source, dry_run):
        tours = Tour.objects.filter(source=source).exclude(highlight="")
        self.stdout.write(f"\nCleaning highlight for {tours.count()} {source} tours...")

        updated = 0
        for tour in tours:
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

    def _clean_itinerary_hotel_names(self, scraper, source, dry_run):
        """Clean hotel_name field — Zego API embeds Font Awesome icons as HTML."""
        days = ItineraryDay.objects.filter(tour__source=source).exclude(hotel_name="")
        self.stdout.write(
            f"\nCleaning itinerary hotel names for {days.count()} {source} days..."
        )

        updated = 0
        for day in days:
            new_hotel = scraper._html_to_text(day.hotel_name)
            if new_hotel != day.hotel_name:
                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {day.tour.product_code} Day {day.day_number}: hotel changed\n"
                        f"    WAS: {repr(day.hotel_name[:80])}\n"
                        f"    NOW: {repr(new_hotel[:80])}"
                    )
                else:
                    day.hotel_name = new_hotel[:300]
                    day.save(update_fields=["hotel_name"])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"  {updated} itinerary hotel names cleaned")
        )

    def _clean_itinerary_meal_descriptions(self, scraper, source, dry_run):
        """Clean breakfast/lunch/dinner_description fields."""
        days = ItineraryDay.objects.filter(tour__source=source).exclude(
            breakfast_description="",
            lunch_description="",
            dinner_description="",
        )
        self.stdout.write(
            f"\nCleaning itinerary meal descriptions for {days.count()} {source} days..."
        )

        updated = 0
        for day in days:
            new_b = scraper._html_to_text(day.breakfast_description)
            new_l = scraper._html_to_text(day.lunch_description)
            new_d = scraper._html_to_text(day.dinner_description)

            if (
                new_b != day.breakfast_description
                or new_l != day.lunch_description
                or new_d != day.dinner_description
            ):
                if dry_run:
                    self.stdout.write(
                        f"  [DRY] {day.tour.product_code} Day {day.day_number}: meal desc changed"
                    )
                else:
                    day.breakfast_description = new_b[:300]
                    day.lunch_description = new_l[:300]
                    day.dinner_description = new_d[:300]
                    day.save(
                        update_fields=[
                            "breakfast_description",
                            "lunch_description",
                            "dinner_description",
                        ]
                    )
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"  {updated} itinerary meal descriptions cleaned")
        )
