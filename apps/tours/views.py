import io

from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import DetailView, ListView

from xhtml2pdf import pisa

from .models import Destination, Tour, TourDeparture


def _has_available_departure():
    """Subquery: tour has at least one available departure."""
    return TourDeparture.objects.filter(tour=OuterRef("pk"), status="available")


class TourListView(ListView):
    model = Tour
    template_name = "tours/tour_list.html"
    context_object_name = "tours"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Tour.objects.filter(status=Tour.Status.PUBLISHED)
            .filter(Exists(_has_available_departure()))
            .select_related("airline")
            .prefetch_related("destinations", "categories")
        )

        # Search
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(title_th__icontains=q)
                | Q(description__icontains=q)
                | Q(short_description__icontains=q)
            )

        # Filter by destination
        dest = self.request.GET.get("destination")
        if dest:
            qs = qs.filter(destinations__slug=dest)

        # Filter by category
        cat = self.request.GET.get("category")
        if cat:
            qs = qs.filter(categories__slug=cat)

        # Filter by max price
        max_price = self.request.GET.get("max_price")
        if max_price:
            try:
                qs = qs.filter(price_from__lte=int(max_price))
            except (ValueError, TypeError):
                pass

        # Filter by duration
        duration = self.request.GET.get("duration")
        if duration:
            try:
                qs = qs.filter(duration_days__lte=int(duration))
            except (ValueError, TypeError):
                pass

        # Sort
        sort = self.request.GET.get("sort", "-is_featured")
        valid_sorts = {
            "price_asc": "price_from",
            "price_desc": "-price_from",
            "newest": "-created_at",
            "duration": "duration_days",
        }
        qs = qs.order_by(valid_sorts.get(sort, "-is_featured"), "-created_at")

        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["destinations"] = Destination.objects.filter(parent__isnull=True)
        ctx["current_filters"] = {
            "q": self.request.GET.get("q", ""),
            "destination": self.request.GET.get("destination", ""),
            "max_price": self.request.GET.get("max_price", ""),
            "duration": self.request.GET.get("duration", ""),
            "sort": self.request.GET.get("sort", ""),
        }
        return ctx


class TourDetailView(DetailView):
    model = Tour
    template_name = "tours/tour_detail.html"
    context_object_name = "tour"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Tour.objects.filter(status=Tour.Status.PUBLISHED)
            .select_related("airline")
            .prefetch_related(
                "images",
                "itinerary_days",
                "price_options",
                "destinations",
                "categories",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tour = self.object

        # Related tours from same destinations (exclude sold-out)
        ctx["related_tours"] = (
            Tour.objects.filter(
                status=Tour.Status.PUBLISHED,
                destinations__in=tour.destinations.all(),
            )
            .filter(Exists(_has_available_departure()))
            .exclude(pk=tour.pk)
            .select_related("airline")
            .prefetch_related("destinations")
            .distinct()[:4]
        )

        # Inquiry form (only add if not already present from form validation error)
        if "inquiry_form" not in ctx:
            from apps.bookings.forms import InquiryForm

            ctx["inquiry_form"] = InquiryForm()

        return ctx


class TourPdfView(DetailView):
    """Generate a downloadable PDF for a tour."""

    model = Tour
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Tour.objects.filter(status=Tour.Status.PUBLISHED)
            .select_related("airline")
            .prefetch_related("itinerary_days", "destinations", "categories")
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        tour = self.object

        departures = tour.departures.filter(status="available").order_by(
            "departure_date"
        )[:10]

        html = render_to_string(
            "tours/tour_pdf.html",
            {
                "tour": tour,
                "departures": departures,
                "itinerary": tour.itinerary_days.all().order_by("day_number"),
            },
        )

        buf = io.BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buf, encoding="utf-8")

        if pisa_status.err:
            return HttpResponse("PDF generation error", status=500)

        buf.seek(0)
        response = HttpResponse(buf.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{tour.slug}.pdf"'
        return response
