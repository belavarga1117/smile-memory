"""Performance tests — N+1 query detection."""

import pytest

from .factories import (
    CategoryFactory,
    DestinationFactory,
    ItineraryDayFactory,
    TourDepartureFactory,
    TourFactory,
    TourImageFactory,
)


@pytest.mark.django_db
class TestQueryPerformance:
    """Ensure views don't produce excessive queries (N+1 detection)."""

    def test_tour_detail_query_count(self, client, django_assert_max_num_queries):
        """Tour detail page should not exceed a reasonable query count."""
        dest = DestinationFactory()
        cat = CategoryFactory()
        tour = TourFactory(destinations=[dest], categories=[cat])
        # Add related objects to trigger potential N+1
        for i in range(3):
            TourDepartureFactory(tour=tour)
            ItineraryDayFactory(tour=tour, day_number=i + 1)
            TourImageFactory(tour=tour)

        # Tour detail with 3 departures, 3 itinerary days, 3 images
        # should stay under ~15 queries (select_related + prefetch_related)
        with django_assert_max_num_queries(20):
            resp = client.get(f"/en/tours/{tour.slug}/")
            assert resp.status_code == 200

    def test_tour_list_query_count(self, client, django_assert_max_num_queries):
        """Tour list page should be efficient with multiple tours."""
        dest = DestinationFactory()
        for _ in range(5):
            TourFactory(destinations=[dest])

        # List page with 5 tours should stay under ~10 queries
        with django_assert_max_num_queries(15):
            resp = client.get("/en/tours/")
            assert resp.status_code == 200

    def test_tour_api_list_query_count(self, client, django_assert_max_num_queries):
        """API list endpoint should be efficient."""
        dest = DestinationFactory()
        for _ in range(5):
            TourFactory(destinations=[dest])

        with django_assert_max_num_queries(15):
            resp = client.get("/api/v1/tours/")
            assert resp.status_code == 200
