from django.contrib import messages
from django.db.models import Count, Exists, OuterRef, Q
from django.views.generic import FormView, TemplateView

from apps.core.spam_protection import check_rate_limit, rate_limit_response
from apps.tours.models import Destination, Tour, TourDeparture

from .forms import ContactForm
from .models import FAQ, HeroSlide, Testimonial, TrustBadge


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hero_slides"] = HeroSlide.objects.filter(is_active=True)
        has_available = TourDeparture.objects.filter(
            tour=OuterRef("pk"), status="available"
        )
        ctx["featured_tours"] = (
            Tour.objects.filter(status=Tour.Status.PUBLISHED, is_featured=True)
            .exclude(pdf_url="")
            .filter(Exists(has_available))
            .select_related("airline")
            .prefetch_related("destinations")[:6]
        )

        # Destinations ordered by published tour count, top 7 + "Others"
        published_filter = Q(
            tours__status=Tour.Status.PUBLISHED
        ) & ~Q(tours__pdf_url="")
        all_dests = (
            Destination.objects.filter(parent__isnull=True)
            .annotate(tour_count=Count("tours", filter=published_filter))
            .filter(tour_count__gt=0)
            .order_by("-tour_count")
        )
        top_destinations = list(all_dests[:7])
        ctx["featured_destinations"] = top_destinations
        ctx["total_tour_count"] = (
            Tour.objects.filter(status=Tour.Status.PUBLISHED)
            .exclude(pdf_url="")
            .filter(Exists(has_available))
            .count()
        )

        ctx["testimonials"] = Testimonial.objects.filter(is_active=True)[:6]
        ctx["trust_badges"] = TrustBadge.objects.all()[:4]
        ctx["faqs"] = FAQ.objects.filter(is_active=True)[:8]
        return ctx


class AboutView(TemplateView):
    template_name = "pages/about.html"


class ContactView(FormView):
    template_name = "pages/contact.html"
    form_class = ContactForm
    success_url = "/contact/"

    def post(self, request, *args, **kwargs):
        if not check_rate_limit(
            request, key="contact_submissions", max_count=3, window=300
        ):
            return rate_limit_response()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request, "Thank you for your message! We'll get back to you soon."
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["faqs"] = FAQ.objects.filter(is_active=True)[:5]
        return ctx


class PaymentInfoView(TemplateView):
    template_name = "pages/payment_info.html"
