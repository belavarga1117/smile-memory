"""Management command to strip product code prefixes and routing junk from tour titles.

Handles all import sources. Each source may embed different junk:
  Real Journey: "RJ-XJ107 ทัวร์ เรียล...ฮอกไกโด"    → "ทัวร์ เรียล...ฮอกไกโด"
  GS25:         "NRT69 XJ DMK TOKYO TULIP 9D7N"       → "TOKYO TULIP"
  Zego:         ": TOUR NAME"                          → "TOUR NAME"

Rules applied in order:
  1. Product code prefix (exact match)
  2. Generic CODE-XXXXX prefix (RJ-XJ107 style)
  3. Zego ': ' prefix convention
  4. GS25: leading IATA airline code (XJ, TK, VZ...) and whitelisted Thai departure airports
  5. GS25: inline ' BY XX' airline pattern
  6. ALL SOURCES: duration codes (9D7N, 5D3N) — redundant since duration_display badge shows this

This command is idempotent — running it twice has no effect.

Usage:
    python manage.py clean_tour_titles            # dry-run (preview only)
    python manage.py clean_tour_titles --apply    # actually update DB
    python manage.py clean_tour_titles --source gs25 --apply
"""

import re

from django.core.management.base import BaseCommand

from apps.tours.models import Tour

# Matches product code prefixes like: RJ-XJ107, GO365-JPN001, ZG-ABC123
# Requires at least one digit after the hyphen to avoid matching place names like NAGOYA-OSAKA
_CODE_PREFIX_RE = re.compile(r"^([A-Z]{1,6}-[A-Z0-9]*\d[A-Z0-9]*)\s+")

# GS25-specific: strip IATA airline codes (2-letter) and known Thai departure airports
_AIRLINE_PREFIX_RE = re.compile(r"^[A-Z]{2}\s+")
# Only whitelist Thai departure airports — prevents "TAM" in "Tam Dao" (Vietnamese place) being stripped
_GS25_DEPART_AIRPORTS = frozenset({"DMK", "BKK", "CNX", "HKT"})
_AIRPORT_PREFIX_RE = re.compile(r"^([A-Z]{3})\s+")
_BY_AIRLINE_RE = re.compile(r"\s+BY\s+[A-Z]{2}\b")

# Universal: duration codes embedded in title slugs (9D7N, 5D3N, 10D7N...)
# These are redundant — the Tour.duration_display badge already shows duration on cards.
_DURATION_CODE_RE = re.compile(r"\s+\d+D\d*N\b", re.IGNORECASE)


def strip_code_prefix(title: str, product_code: str = "", source: str = "") -> str:
    """Return title with leading product-code prefix removed.

    Priority:
    1. If title starts with the tour's own product_code, strip that exactly.
    2. Fall back to generic UPPER-ALPHANUM pattern (catches future scrapers).
    3. Strip Zego's ': ' prefix from Tour_Name API field (portal convention).
    4. For GS25: also strip leading airline/airport IATA codes and BY XX patterns.
    """
    if not title:
        return title

    # Exact match against stored product_code (most reliable)
    if product_code and title.startswith(product_code + " "):
        title = title[len(product_code) :].lstrip()
        # Zego portal convention: product code may be followed by ': <title>'
        if title.startswith(": "):
            title = title[2:].lstrip()
    else:
        # Generic pattern fallback: CODE-XXXXX <title>
        m = _CODE_PREFIX_RE.match(title)
        if m:
            title = title[m.end() :]

        # Zego portal convention: Tour_Name field may start with ': <title>'
        elif title.startswith(": "):
            title = title[2:].lstrip()

    # GS25: strip leading airline codes (XJ, TK...) and whitelisted Thai departure airports.
    # Run airport→airline→airport to handle both orderings (XJ DMK or DMK XJ).
    if source == "gs25":

        def _strip_airport(t):
            m = _AIRPORT_PREFIX_RE.match(t)
            if m and m.group(1) in _GS25_DEPART_AIRPORTS:
                return t[m.end() :]
            return t

        title = _strip_airport(title)
        title = _AIRLINE_PREFIX_RE.sub("", title)
        title = _strip_airport(title)
        title = _BY_AIRLINE_RE.sub("", title)

    # ALL SOURCES: strip embedded duration codes (9D7N, 5D3N...) — already shown via duration_display.
    title = _DURATION_CODE_RE.sub("", title)

    return title.strip()


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
            new_title = strip_code_prefix(tour.title, tour.product_code, tour.source)
            new_title_th = strip_code_prefix(
                tour.title_th or "", tour.product_code, tour.source
            )

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
