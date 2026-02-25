"""Fill missing Thai translations for Destination, Category, and Airline models."""

from django.core.management.base import BaseCommand

from apps.tours.models import Airline, Category, Destination
from apps.tours.th_names import AIRLINE_TH, CATEGORY_TH, DESTINATION_TH


class Command(BaseCommand):
    help = "Fill missing Thai translations for Destination, Category, and Airline"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without saving",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nem ment semmit\n"))

        self._fill_model(Destination, "name", "name_th", DESTINATION_TH, dry_run)
        self._fill_model(Category, "name", "name_th", CATEGORY_TH, dry_run)
        self._fill_model(Airline, "name", "name_th", AIRLINE_TH, dry_run)

    def _fill_model(self, model, en_field, th_field, mapping, dry_run):
        model_name = model.__name__
        updated = 0
        skipped = 0
        unknown = []

        for obj in model.objects.all():
            en_value = getattr(obj, en_field)
            th_value = getattr(obj, th_field)

            if th_value:
                skipped += 1
                continue

            if en_value in mapping:
                new_th = mapping[en_value]
                if not dry_run:
                    setattr(obj, th_field, new_th)
                    obj.save(update_fields=[th_field])
                self.stdout.write(
                    f"  {'[DRY] ' if dry_run else ''}✅ {model_name}: {en_value} → {new_th}"
                )
                updated += 1
            else:
                unknown.append(en_value)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{model_name}: {updated} frissítve, {skipped} már megvolt"
            )
        )
        if unknown:
            self.stdout.write(
                self.style.WARNING(
                    f"  Ismeretlen (kézi fordítás kell): {', '.join(unknown)}"
                )
            )
