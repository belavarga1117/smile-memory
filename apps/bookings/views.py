import logging

from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language
from django.views import View

from apps.core.spam_protection import check_rate_limit, rate_limit_response
from apps.customers.models import Customer
from apps.tours.models import Tour, TourDeparture

from .forms import InquiryForm
from .models import Inquiry
from .notifications import send_inquiry_notification_to_admin, send_inquiry_thank_you

logger = logging.getLogger(__name__)


class InquiryCreateView(View):
    """Handle tour inquiry submission."""

    def post(self, request, slug):
        if not check_rate_limit(
            request, key="inquiry_submissions", max_count=5, window=300
        ):
            return rate_limit_response()
        tour = get_object_or_404(Tour, slug=slug, status=Tour.Status.PUBLISHED)
        form = InquiryForm(request.POST)

        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.tour = tour
            inquiry.language = get_language() or "th"

            # Link departure if specified
            departure_id = request.POST.get("departure_id")
            if departure_id:
                try:
                    inquiry.departure = TourDeparture.objects.get(
                        pk=departure_id, tour=tour
                    )
                except TourDeparture.DoesNotExist:
                    pass

            # Get or create customer
            customer, created = Customer.objects.get_or_create(
                email=inquiry.contact_email,
                defaults={
                    "first_name": inquiry.contact_name.split()[0]
                    if inquiry.contact_name
                    else "",
                    "last_name": " ".join(inquiry.contact_name.split()[1:])
                    if inquiry.contact_name
                    else "",
                    "phone": inquiry.contact_phone,
                },
            )

            # Update marketing opt-in
            if inquiry.marketing_opt_in and not customer.marketing_opt_in:
                customer.marketing_opt_in = True
                customer.opted_in_at = timezone.now()

            # Update stats
            customer.total_inquiries += 1
            customer.save()

            inquiry.customer = customer
            inquiry.save()

            # Send notifications (best-effort, don't block on failure)
            try:
                send_inquiry_thank_you(inquiry)
                send_inquiry_notification_to_admin(inquiry)
            except Exception:
                logger.error(
                    "Email notification failed for inquiry %s",
                    inquiry.reference_number,
                    exc_info=True,
                )

            return redirect("bookings:success", reference=inquiry.reference_number)

        # If form invalid, re-render the tour detail page with errors
        from apps.tours.views import TourDetailView

        view = TourDetailView()
        view.request = request
        view.kwargs = {"slug": slug}
        view.object = tour
        ctx = view.get_context_data(object=tour)
        ctx["inquiry_form"] = form
        return render(request, "tours/tour_detail.html", ctx)


class InquirySuccessView(View):
    """Simple thank-you page after inquiry submission."""

    def get(self, request, reference):
        inquiry = get_object_or_404(
            Inquiry.objects.select_related("customer", "tour", "departure"),
            reference_number=reference,
        )
        return render(request, "bookings/inquiry_success.html", {"inquiry": inquiry})
