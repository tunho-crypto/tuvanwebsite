from django.urls import path

from baocao import views

app_name = "baocao"
urlpatterns = [
    path("", views.BaoCaoView.as_view(), name="bao_cao"),
    path("cay-trong/", views.CayTrongXuatView.as_view(), name="cay_trong"),
    path("luat-tu-van/", views.LuatXuatView.as_view(), name="luat"),
    path("lich-su-tu-van/", views.LichSuXuatView.as_view(), name="lich_su"),
]
