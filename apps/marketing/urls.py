from django.urls import path

from . import views

app_name = "marketing"

urlpatterns = [
    path("subscribe/", views.NewsletterSubscribeView.as_view(), name="subscribe"),
    path(
        "unsubscribe/<uuid:token>/",
        views.NewsletterUnsubscribeView.as_view(),
        name="unsubscribe",
    ),
]
