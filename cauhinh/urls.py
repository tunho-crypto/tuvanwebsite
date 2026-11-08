from django.urls import path

from cauhinh import views

app_name = "cauhinh"
urlpatterns = [
    path("", views.TrongSoView.as_view(), name="trong_so"),
]
