from django.urls import path, register_converter

from danhmuc import views


class MucConverter:
    """Chỉ nhận 5 slug danh mục hợp lệ."""

    regex = "|".join(views.CAU_HINH_DANH_MUC)

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(MucConverter, "muc")

app_name = "danhmuc"
urlpatterns = [
    path("<muc:muc>/", views.DanhMucDanhSachView.as_view(), name="ds"),
    path("<muc:muc>/them/", views.DanhMucThemView.as_view(), name="them"),
    path("<muc:muc>/<int:pk>/sua/", views.DanhMucSuaView.as_view(), name="sua"),
    path("<muc:muc>/<int:pk>/xoa/", views.DanhMucXoaView.as_view(), name="xoa"),
]
