from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("inquire/<slug:slug>/", views.InquiryCreateView.as_view(), name="inquire"),
    path(
        "success/<str:reference>/", views.InquirySuccessView.as_view(), name="success"
    ),
]
