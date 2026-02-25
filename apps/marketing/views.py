from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.core.spam_protection import check_rate_limit, rate_limit_response
from apps.customers.models import Customer

from .models import Subscriber


class NewsletterSubscribeView(View):
    """Handle newsletter signup from footer or standalone form."""

    def post(self, request):
        if not check_rate_limit(
            request, key="subscribe_submissions", max_count=3, window=300
        ):
            return rate_limit_response()

        # Honeypot check
        if request.POST.get("website_url", ""):
            return redirect(request.META.get("HTTP_REFERER", "/"))

        email = request.POST.get("email", "").strip().lower()
        source = request.POST.get("source", "footer")

        if not email:
            messages.error(request, "Please enter a valid email address.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        # Create or update subscriber
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={"source": source, "is_active": True},
        )
        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])

        # Link to customer if exists
        try:
            customer = Customer.objects.get(email=email)
            subscriber.customer = customer
            subscriber.save(update_fields=["customer"])
            if not customer.marketing_opt_in:
                customer.marketing_opt_in = True
                customer.opted_in_at = timezone.now()
                customer.save(update_fields=["marketing_opt_in", "opted_in_at"])
        except Customer.DoesNotExist:
            pass

        messages.success(
            request,
            "Thank you for subscribing! You'll receive our latest tour deals and travel tips.",
        )
        return redirect(request.META.get("HTTP_REFERER", "/"))


class NewsletterUnsubscribeView(View):
    """Handle newsletter unsubscribe via unique token."""

    def get(self, request, token):
        subscriber = get_object_or_404(Subscriber, unsubscribe_token=token)
        return render(
            request,
            "marketing/unsubscribe_confirm.html",
            {
                "subscriber": subscriber,
            },
        )

    def post(self, request, token):
        subscriber = get_object_or_404(Subscriber, unsubscribe_token=token)
        subscriber.is_active = False
        subscriber.save(update_fields=["is_active"])

        # Also update customer opt-in
        if subscriber.customer:
            subscriber.customer.marketing_opt_in = False
            subscriber.customer.save(update_fields=["marketing_opt_in"])

        messages.success(
            request,
            "You have been unsubscribed. You will no longer receive marketing emails from us.",
        )
        return render(
            request,
            "marketing/unsubscribe_done.html",
            {
                "subscriber": subscriber,
            },
        )
