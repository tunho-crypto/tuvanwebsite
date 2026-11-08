from django.urls import path

from hoidap import views

app_name = "hoidap"
urlpatterns = [
    path("", views.CauHoiDanhSachView.as_view(), name="ds"),
    path("them/", views.CauHoiThemView.as_view(), name="them"),
    path("<int:pk>/", views.CauHoiChiTietView.as_view(), name="chi_tiet"),
    path("<int:pk>/tra-loi/", views.TraLoiView.as_view(), name="tra_loi"),
]
