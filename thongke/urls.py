from django.urls import path

from thongke import views

app_name = "thongke"
urlpatterns = [
    path("", views.ThongKeView.as_view(), name="thong_ke"),
]
