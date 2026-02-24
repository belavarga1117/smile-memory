from django.contrib import messages
from django.views.generic import FormView, TemplateView

from apps.tours.models import Destination, Tour

from .forms import ContactForm
from .models import FAQ, HeroSlide, Testimonial, TrustBadge


class HomePageView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["hero_slides"] = HeroSlide.objects.filter(is_active=True)
        ctx["featured_tours"] = (
            Tour.objects.filter(status=Tour.Status.PUBLISHED, is_featured=True)
            .select_related("airline")
            .prefetch_related("destinations")[:6]
        )
        ctx["featured_destinations"] = Destination.objects.filter(
            is_featured=True, parent__isnull=True
        )[:8]
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
