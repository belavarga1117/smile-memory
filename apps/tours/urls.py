from django.urls import path

from . import views

app_name = "tours"

urlpatterns = [
    path("", views.TourListView.as_view(), name="list"),
    path("<slug:slug>/", views.TourDetailView.as_view(), name="detail"),
    path("<slug:slug>/pdf/", views.TourPdfView.as_view(), name="pdf"),
]
