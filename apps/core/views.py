"""Core views — admin dashboard."""

from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from apps.bookings.models import Inquiry
from apps.customers.models import Customer
from apps.importer.models import ImportJob
from apps.marketing.models import Campaign, Subscriber
from apps.tours.models import Destination, Tour, TourDeparture


@method_decorator(staff_member_required, name="dispatch")
class DashboardView(TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # --- KPI cards ---
        ctx["total_tours"] = Tour.objects.filter(status="published").count()
        ctx["total_drafts"] = Tour.objects.filter(status="draft").count()
        ctx["total_inquiries"] = Inquiry.objects.count()
        ctx["new_inquiries"] = Inquiry.objects.filter(status="new").count()
        ctx["total_customers"] = Customer.objects.count()
        ctx["opted_in_customers"] = Customer.objects.filter(
            marketing_opt_in=True
        ).count()
        ctx["total_subscribers"] = Subscriber.objects.filter(is_active=True).count()
        ctx["total_campaigns"] = Campaign.objects.filter(status="sent").count()

        # Month-over-month inquiries
        ctx["inquiries_this_month"] = Inquiry.objects.filter(
            created_at__gte=thirty_days_ago
        ).count()

        # --- Inquiry status breakdown (for pie chart) ---
        status_qs = (
            Inquiry.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        ctx["inquiry_statuses"] = list(status_qs)

        # --- Monthly inquiry trend (last 6 months, for line chart) ---
        monthly_data = []
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if i > 0:
                month_end = (now - timedelta(days=30 * (i - 1))).replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )
            else:
                month_end = now
            count = Inquiry.objects.filter(
                created_at__gte=month_start, created_at__lt=month_end
            ).count()
            monthly_data.append(
                {"month": month_start.strftime("%b %Y"), "count": count}
            )
        ctx["monthly_inquiries"] = monthly_data

        # --- Top destinations by tour count ---
        ctx["top_destinations"] = (
            Destination.objects.annotate(tour_count=Count("tours"))
            .filter(tour_count__gt=0)
            .order_by("-tour_count")[:8]
        )

        # --- Upcoming departures ---
        ctx["upcoming_departures"] = (
            TourDeparture.objects.filter(
                departure_date__gte=now.date(),
                status="available",
            )
            .select_related("tour")
            .order_by("departure_date")[:10]
        )

        # --- Recent inquiries ---
        ctx["recent_inquiries"] = Inquiry.objects.select_related(
            "customer", "tour"
        ).order_by("-created_at")[:10]

        # --- Recent imports ---
        ctx["recent_imports"] = ImportJob.objects.order_by("-created_at")[:5]

        # --- Revenue estimate (confirmed inquiries with quoted_price) ---
        revenue = Inquiry.objects.filter(status="confirmed").aggregate(
            total=Sum("quoted_price")
        )
        ctx["total_revenue"] = revenue["total"] or 0

        return ctx
