from django import forms

from .models import Inquiry

INPUT_CLASS = (
    "w-full px-4 py-3 rounded-lg border border-gray-300 "
    "focus:ring-2 focus:ring-aqua-500 focus:border-transparent text-sm"
)
SELECT_CLASS = INPUT_CLASS


class InquiryForm(forms.ModelForm):
    """Public-facing inquiry form shown on tour detail page."""

    class Meta:
        model = Inquiry
        fields = [
            "contact_name",
            "contact_email",
            "contact_phone",
            "num_adults",
            "num_children",
            "num_infants",
            "room_preference",
            "special_requests",
            "marketing_opt_in",
        ]
        widgets = {
            "contact_name": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "Your full name",
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "your@email.com",
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": INPUT_CLASS,
                    "placeholder": "+66 XX XXX XXXX",
                }
            ),
            "num_adults": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 1,
                    "max": 20,
                }
            ),
            "num_children": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 0,
                    "max": 20,
                }
            ),
            "num_infants": forms.NumberInput(
                attrs={
                    "class": INPUT_CLASS,
                    "min": 0,
                    "max": 10,
                }
            ),
            "room_preference": forms.Select(
                choices=[
                    ("", "Select room type"),
                    ("double", "Double Room"),
                    ("twin", "Twin Room"),
                    ("single", "Single Room"),
                    ("triple", "Triple Room"),
                ],
                attrs={"class": SELECT_CLASS},
            ),
            "special_requests": forms.Textarea(
                attrs={
                    "class": INPUT_CLASS,
                    "rows": 3,
                    "placeholder": "Any special requirements (dietary, mobility, etc.)",
                }
            ),
            "marketing_opt_in": forms.CheckboxInput(
                attrs={
                    "class": "w-4 h-4 text-aqua-500 border-gray-300 rounded focus:ring-aqua-500",
                }
            ),
        }
        labels = {
            "contact_name": "Full Name",
            "contact_email": "Email",
            "contact_phone": "Phone",
            "num_adults": "Adults",
            "num_children": "Children (2-11)",
            "num_infants": "Infants (0-2)",
            "room_preference": "Room Preference",
            "special_requests": "Special Requests",
            "marketing_opt_in": "I'd like to receive tour deals and travel tips via email",
        }
