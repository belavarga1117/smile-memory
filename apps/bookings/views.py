from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.customers.models import Customer
from apps.tours.models import Tour, TourDeparture

from .forms import InquiryForm
from .models import Inquiry
from .notifications import send_inquiry_notification_to_admin, send_inquiry_thank_you


class InquiryCreateView(View):
    """Handle tour inquiry submission."""

    def post(self, request, slug):
        tour = get_object_or_404(Tour, slug=slug, status=Tour.Status.PUBLISHED)
        form = InquiryForm(request.POST)

        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.tour = tour

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
                pass  # Email failures shouldn't break the inquiry

            messages.success(
                request,
                f"Thank you! Your inquiry ({inquiry.reference_number}) has been submitted. "
                "We'll get back to you within 24 hours.",
            )
            return redirect(tour.get_absolute_url())

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
