"""Database integrity and migration sanity tests."""

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.db import IntegrityError

from apps.tours.models import (
    Destination,
    ItineraryDay,
    TourDeparture,
    TourImage,
)

from .factories import (
    ItineraryDayFactory,
    TourDepartureFactory,
    TourFactory,
    TourImageFactory,
)


@pytest.mark.django_db
class TestUniqueConstraints:
    """Verify critical unique constraints are enforced at DB level."""

    def test_tour_product_code_unique(self):
        TourFactory(product_code="UNIQUE-001")
        with pytest.raises(IntegrityError):
            TourFactory(product_code="UNIQUE-001")

    def test_destination_slug_unique(self):
        Destination.objects.create(name="Test A", slug="japan-unique")
        with pytest.raises(IntegrityError):
            Destination.objects.create(name="Test B", slug="japan-unique")

    def test_itinerary_day_unique_together(self):
        """tour + day_number must be unique together."""
        tour = TourFactory()
        ItineraryDayFactory(tour=tour, day_number=1)
        with pytest.raises(IntegrityError):
            ItineraryDayFactory(tour=tour, day_number=1)


@pytest.mark.django_db
class TestForeignKeyCascade:
    """Verify FK ON DELETE behavior is correct."""

    def test_tour_delete_cascades_departures(self):
        tour = TourFactory()
        TourDepartureFactory(tour=tour)
        TourDepartureFactory(tour=tour)
        tour_pk = tour.pk

        assert TourDeparture.objects.filter(tour_id=tour_pk).count() == 2
        tour.delete()
        assert TourDeparture.objects.filter(tour_id=tour_pk).count() == 0

    def test_tour_delete_cascades_images(self):
        tour = TourFactory()
        TourImageFactory(tour=tour)
        tour_pk = tour.pk

        assert TourImage.objects.filter(tour_id=tour_pk).count() == 1
        tour.delete()
        assert TourImage.objects.filter(tour_id=tour_pk).count() == 0

    def test_tour_delete_cascades_itinerary(self):
        tour = TourFactory()
        ItineraryDayFactory(tour=tour, day_number=1)
        tour_pk = tour.pk

        tour.delete()
        assert ItineraryDay.objects.filter(tour_id=tour_pk).count() == 0


@pytest.mark.django_db
class TestMigrationSanity:
    """Verify migrations are consistent and complete."""

    def test_no_pending_migrations(self):
        """All migrations should be applied — no unapplied changes."""
        # This calls Django's migration checker
        try:
            call_command("migrate", "--check", verbosity=0)
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(
                    "There are unapplied migrations. Run: python manage.py migrate"
                )

    def test_makemigrations_no_changes(self):
        """No model changes should be unmigrated."""
        try:
            call_command("makemigrations", "--check", "--dry-run", verbosity=0)
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(
                    "Model changes detected without migrations. "
                    "Run: python manage.py makemigrations"
                )


@pytest.mark.django_db
class TestDataIntegrity:
    """Test pricing and data quality rules."""

    def test_price_from_is_positive(self):
        tour = TourFactory(price_from=Decimal("29900"))
        assert tour.price_from > 0

    def test_departure_effective_price_uses_promo_when_lower(self):
        dep = TourDepartureFactory(
            price_adult=Decimal("29900"),
            price_child=Decimal("25900"),
        )
        dep.price_adult_promo = Decimal("24900")
        dep.save()
        assert dep.effective_price == Decimal("24900")

    def test_departure_effective_price_ignores_higher_promo(self):
        dep = TourDepartureFactory(price_adult=Decimal("29900"))
        dep.price_adult_promo = Decimal("39900")
        dep.save()
        assert dep.effective_price == Decimal("29900")

    def test_update_price_from_uses_min_departure_price(self):
        tour = TourFactory(price_from=Decimal("50000"))
        TourDepartureFactory(
            tour=tour,
            price_adult=Decimal("19900"),
            status=TourDeparture.PeriodStatus.AVAILABLE,
        )
        TourDepartureFactory(
            tour=tour,
            price_adult=Decimal("29900"),
            status=TourDeparture.PeriodStatus.AVAILABLE,
        )
        tour.update_price_from()
        tour.refresh_from_db()
        assert tour.price_from == Decimal("19900")
