from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import get_language
from django.views import View

from apps.core.spam_protection import check_rate_limit, rate_limit_response
from apps.customers.models import Customer

from .models import Subscriber
from .notifications import send_newsletter_confirmation, send_newsletter_welcome


class NewsletterSubscribeView(View):
    """Handle newsletter signup from footer or standalone form (double opt-in)."""

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
        lang = get_language() or "th"

        if not email:
            messages.error(request, "Please enter a valid email address.")
            return redirect(request.META.get("HTTP_REFERER", "/"))

        # Create or update subscriber
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={"source": source, "is_active": True, "language": lang},
        )
        if not created and not subscriber.is_active:
            # Reactivating unsubscribed user — reset confirmation and resend
            subscriber.is_active = True
            subscriber.is_confirmed = False
            subscriber.language = lang
            subscriber.save(update_fields=["is_active", "is_confirmed", "language"])
            created = True

        # Send confirmation email on first signup / reactivation
        # Customer opt-in set only after confirmation (NewsletterConfirmView)
        if created:
            try:
                send_newsletter_confirmation(subscriber)
            except Exception:
                pass

        msg = (
            "ขอบคุณ! กรุณาตรวจสอบอีเมลของท่านเพื่อยืนยันการสมัครรับข่าวสาร"
            if lang == "th"
            else "Thank you! Please check your email to confirm your subscription."
        )
        messages.success(request, msg)
        return redirect(request.META.get("HTTP_REFERER", "/"))


class NewsletterConfirmView(View):
    """Handle double opt-in confirmation link from email."""

    def get(self, request, token):
        subscriber = get_object_or_404(Subscriber, confirmation_token=token)

        if not subscriber.is_confirmed:
            subscriber.is_confirmed = True
            subscriber.confirmed_at = timezone.now()
            subscriber.save(update_fields=["is_confirmed", "confirmed_at"])

            # Now link customer and set marketing opt-in
            try:
                customer = Customer.objects.get(email=subscriber.email)
                if subscriber.customer != customer:
                    subscriber.customer = customer
                    subscriber.save(update_fields=["customer"])
                if not customer.marketing_opt_in:
                    customer.marketing_opt_in = True
                    customer.opted_in_at = timezone.now()
                    customer.save(update_fields=["marketing_opt_in", "opted_in_at"])
            except Customer.DoesNotExist:
                pass

            # Send welcome email now that confirmation is complete
            try:
                send_newsletter_welcome(subscriber)
            except Exception:
                pass

        return render(
            request,
            "marketing/confirm_success.html",
            {"subscriber": subscriber},
        )


class NewsletterUnsubscribeView(View):
    """Handle newsletter unsubscribe via unique token."""

    def get(self, request, token):
        subscriber = get_object_or_404(Subscriber, unsubscribe_token=token)
        return render(
            request,
            "marketing/unsubscribe_confirm.html",
            {"subscriber": subscriber},
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
            {"subscriber": subscriber},
        )
