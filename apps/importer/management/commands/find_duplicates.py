"""Scan the database for duplicate tour data and report findings.

Checks:
1. Tours with duplicate product_code (same code, multiple records)
2. Tours with same title + source (possible double-import)
3. ItineraryDay with duplicate tour+day_number combinations
4. TourDeparture with duplicate tour+departure_date combinations
5. TourImage with duplicate tour+image_url combinations

Usage:
    python manage.py find_duplicates
    python manage.py find_duplicates --fix   # Remove exact duplicates (keeps latest)
"""

from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = "Scan for duplicate tour records and report (optionally fix) them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Remove duplicate records (keeps the latest by ID). Use with caution.",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        total_issues = 0

        if fix:
            self.stdout.write(self.style.WARNING("FIX MODE — will delete duplicates\n"))
        else:
            self.stdout.write(
                self.style.WARNING("DRY RUN — reporting only (use --fix to remove)\n")
            )

        total_issues += self._check_duplicate_product_codes(fix)
        total_issues += self._check_duplicate_titles(fix)
        total_issues += self._check_duplicate_itinerary_days(fix)
        total_issues += self._check_duplicate_departures(fix)
        total_issues += self._check_duplicate_images(fix)

        self.stdout.write("")
        if total_issues == 0:
            self.stdout.write(
                self.style.SUCCESS("No duplicates found — database is clean!")
            )
        else:
            action = "fixed" if fix else "found"
            self.stdout.write(
                self.style.WARNING(f"Total duplicate groups {action}: {total_issues}")
            )

    def _check_duplicate_product_codes(self, fix):
        from apps.tours.models import Tour

        dupes = (
            Tour.objects.values("product_code")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .exclude(product_code="")
            .order_by("-cnt")
        )

        self.stdout.write(f"\n[1] Duplicate product_codes: {dupes.count()} groups")
        issues = 0
        for d in dupes:
            tours = Tour.objects.filter(product_code=d["product_code"]).order_by("id")
            sources = list(tours.values_list("source", flat=True))
            self.stdout.write(
                f"  product_code={d['product_code']} ({d['cnt']} records) "
                f"sources={sources}"
            )
            for t in tours:
                self.stdout.write(
                    f"    ID={t.id} source={t.source} title={t.title[:60]}"
                )
            if fix:
                # Keep the first (oldest), delete the rest
                to_delete = tours[1:]
                deleted_count = len(to_delete)
                Tour.objects.filter(id__in=[t.id for t in to_delete]).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    Deleted {deleted_count} duplicate(s)")
                )
            issues += 1

        if issues == 0:
            self.stdout.write(self.style.SUCCESS("  None found"))
        return issues

    def _check_duplicate_titles(self, fix):
        from apps.tours.models import Tour

        dupes = (
            Tour.objects.values("title", "source")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .exclude(title="")
            .order_by("-cnt")
        )

        self.stdout.write(
            f"\n[2] Duplicate title+source combinations: {dupes.count()} groups"
        )
        issues = 0
        for d in dupes[:20]:  # Limit output to top 20
            tours = Tour.objects.filter(title=d["title"], source=d["source"]).order_by(
                "id"
            )
            self.stdout.write(
                f"  title={d['title'][:60]!r} source={d['source']} ({d['cnt']} records)"
            )
            for t in tours:
                self.stdout.write(
                    f"    ID={t.id} code={t.product_code} external_id={t.external_id}"
                )
            if fix:
                to_delete = tours[1:]
                deleted_count = len(to_delete)
                Tour.objects.filter(id__in=[t.id for t in to_delete]).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    Deleted {deleted_count} duplicate(s)")
                )
            issues += 1

        if dupes.count() > 20:
            self.stdout.write(f"  ... and {dupes.count() - 20} more groups (truncated)")
        if issues == 0:
            self.stdout.write(self.style.SUCCESS("  None found"))
        return issues

    def _check_duplicate_itinerary_days(self, fix):
        from apps.tours.models import ItineraryDay

        dupes = (
            ItineraryDay.objects.values("tour_id", "day_number")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("-cnt")
        )

        self.stdout.write(
            f"\n[3] Duplicate ItineraryDay (tour+day_number): {dupes.count()} groups"
        )
        issues = 0
        for d in dupes[:20]:
            days = ItineraryDay.objects.filter(
                tour_id=d["tour_id"], day_number=d["day_number"]
            ).order_by("id")
            tour_code = days.first().tour.product_code if days.exists() else "?"
            self.stdout.write(
                f"  tour={tour_code} day={d['day_number']} ({d['cnt']} records)"
            )
            if fix:
                to_delete = days[1:]
                deleted_count = len(to_delete)
                ItineraryDay.objects.filter(id__in=[t.id for t in to_delete]).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    Deleted {deleted_count} duplicate(s)")
                )
            issues += 1

        if issues == 0:
            self.stdout.write(self.style.SUCCESS("  None found"))
        return issues

    def _check_duplicate_departures(self, fix):
        from apps.tours.models import TourDeparture

        dupes = (
            TourDeparture.objects.values("tour_id", "departure_date")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .order_by("-cnt")
        )

        self.stdout.write(
            f"\n[4] Duplicate TourDeparture (tour+date): {dupes.count()} groups"
        )
        issues = 0
        for d in dupes[:20]:
            deps = TourDeparture.objects.filter(
                tour_id=d["tour_id"], departure_date=d["departure_date"]
            ).order_by("id")
            tour_code = deps.first().tour.product_code if deps.exists() else "?"
            self.stdout.write(
                f"  tour={tour_code} date={d['departure_date']} ({d['cnt']} records)"
            )
            if fix:
                to_delete = deps[1:]
                deleted_count = len(to_delete)
                TourDeparture.objects.filter(id__in=[t.id for t in to_delete]).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    Deleted {deleted_count} duplicate(s)")
                )
            issues += 1

        if issues == 0:
            self.stdout.write(self.style.SUCCESS("  None found"))
        return issues

    def _check_duplicate_images(self, fix):
        from apps.tours.models import TourImage

        dupes = (
            TourImage.objects.values("tour_id", "image_url")
            .annotate(cnt=Count("id"))
            .filter(cnt__gt=1)
            .exclude(image_url="")
            .order_by("-cnt")
        )

        self.stdout.write(
            f"\n[5] Duplicate TourImage (tour+image_url): {dupes.count()} groups"
        )
        issues = 0
        for d in dupes[:20]:
            imgs = TourImage.objects.filter(
                tour_id=d["tour_id"], image_url=d["image_url"]
            ).order_by("id")
            tour_code = imgs.first().tour.product_code if imgs.exists() else "?"
            self.stdout.write(
                f"  tour={tour_code} url={d['image_url'][:60]} ({d['cnt']} records)"
            )
            if fix:
                to_delete = imgs[1:]
                deleted_count = len(to_delete)
                TourImage.objects.filter(id__in=[t.id for t in to_delete]).delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    Deleted {deleted_count} duplicate(s)")
                )
            issues += 1

        if issues == 0:
            self.stdout.write(self.style.SUCCESS("  None found"))
        return issues
