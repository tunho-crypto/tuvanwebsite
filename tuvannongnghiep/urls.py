from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

handler404 = "taikhoan.views.trang_loi_404"
handler500 = "taikhoan.views.trang_loi_500"

urlpatterns = [
    path("danh-muc/", include("danhmuc.urls")),
    path("tu-van/", include("tuvan.urls")),
    path("tim-kiem/", include("timkiem.urls")),
    path("hoi-dap/", include("hoidap.urls")),
    path("truy-xuat/", include("truyxuat.urls")),
    path("cau-hinh/", include("cauhinh.urls")),
    path("bao-cao/thong-ke/", include("thongke.urls")),  # đặt trước «bao-cao/» để không bị nuốt
    path("bao-cao/", include("baocao.urls")),
    path("", include("taikhoan.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
