from django import forms

from apps.core.spam_protection import HoneypotFormMixin

from .models import ContactMessage


class ContactForm(HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "subject", "message"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-aqua-500 focus:border-transparent",
                    "placeholder": "Your name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-aqua-500 focus:border-transparent",
                    "placeholder": "your@email.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-aqua-500 focus:border-transparent",
                    "placeholder": "+66 XX XXX XXXX",
                }
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-aqua-500 focus:border-transparent",
                    "placeholder": "How can we help?",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-aqua-500 focus:border-transparent",
                    "rows": 5,
                    "placeholder": "Tell us about your travel plans...",
                }
            ),
        }
