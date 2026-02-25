"""Management command to strip product code prefixes from tour titles.

Some scrapers (Real Journey) embed the product code at the start of the tour
title in the source API, e.g.:
  "RJ-XJ107 ทัวร์ เรียล เรียล...ฮอกไกโด"  →  "ทัวร์ เรียล เรียล...ฮอกไกโด"

This command finds all such titles and strips the prefix, both from `title`
and `title_th`. It is idempotent — running it twice has no effect.

Usage:
    python manage.py clean_tour_titles            # dry-run (preview only)
    python manage.py clean_tour_titles --apply    # actually update DB
    python manage.py clean_tour_titles --source realjourney --apply
"""

import re

from django.core.management.base import BaseCommand

from apps.tours.models import Tour

# Matches patterns like: RJ-XJ107, RJ-VZCTS001, GO365-JPN001, ZG-ABC123
_CODE_PREFIX_RE = re.compile(r"^([A-Z]{1,6}-[A-Z0-9]+)\s+")


def strip_code_prefix(title: str, product_code: str = "") -> str:
    """Return title with leading product-code prefix removed.

    Priority:
    1. If title starts with the tour's own product_code, strip that exactly.
    2. Fall back to generic UPPER-ALPHANUM pattern (catches future scrapers).
    3. Strip Zego's ': ' prefix from Tour_Name API field (portal convention).
    """
    if not title:
        return title

    # Exact match against stored product_code (most reliable)
    if product_code and title.startswith(product_code + " "):
        return title[len(product_code) :].lstrip()

    # Generic pattern fallback: CODE-XXXXX <title>
    m = _CODE_PREFIX_RE.match(title)
    if m:
        return title[m.end() :]

    # Zego portal convention: Tour_Name field may start with ': <title>'
    if title.startswith(": "):
        return title[2:].lstrip()

    return title


class Command(BaseCommand):
    help = "Strip product code prefixes from tour titles (e.g. 'RJ-XJ107 ทัวร์...' → 'ทัวร์...')"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Actually update the database (default: dry-run preview only)",
        )
        parser.add_argument(
            "--source",
            type=str,
            default=None,
            help="Limit to a specific source (e.g. realjourney, go365, zego)",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        source_filter = options["source"]

        qs = Tour.objects.all()
        if source_filter:
            qs = qs.filter(source=source_filter)

        changed = []
        for tour in qs.iterator():
            new_title = strip_code_prefix(tour.title, tour.product_code)
            new_title_th = strip_code_prefix(tour.title_th or "", tour.product_code)

            title_changed = new_title != tour.title
            title_th_changed = new_title_th != (tour.title_th or "")

            if title_changed or title_th_changed:
                changed.append((tour, new_title, new_title_th))
                self.stdout.write(
                    f"  [{tour.source}] [{tour.product_code}]\n"
                    f"    title:    {tour.title[:70]!r}\n"
                    f"    → {new_title[:70]!r}\n"
                )

        if not changed:
            self.stdout.write(self.style.SUCCESS("No titles need cleaning."))
            return

        self.stdout.write(f"\nFound {len(changed)} tour(s) to clean.")

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "\nDry-run mode — no changes written. "
                    "Re-run with --apply to update the database."
                )
            )
            return

        updated = 0
        for tour, new_title, new_title_th in changed:
            tour.title = new_title
            if tour.title_th:
                tour.title_th = new_title_th
            tour.save(update_fields=["title", "title_th", "updated_at"])
            updated += 1

        self.stdout.write(self.style.SUCCESS(f"Cleaned {updated} tour title(s)."))
