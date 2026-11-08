from django.urls import path

from truyxuat import views

app_name = "truyxuat"
urlpatterns = [
    path("", views.TruyXuatView.as_view(), name="truy_xuat"),
]
