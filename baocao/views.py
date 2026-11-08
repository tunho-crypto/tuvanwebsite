"""Báo cáo Excel. Chỉ ADMIN (mục 6: «báo cáo và mọi Excel»). Mỗi lần xuất được ghi nhật ký."""
from django.shortcuts import redirect
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView

from baocao import services
from baocao.excel import phan_hoi_xlsx, ten_tep, tao_xlsx
from danhmuc.models import CayTrong
from taikhoan.models import NhatKy
from taikhoan.permissions import QuanTriMixin
from thongke.forms import LocThoiGianForm
from tuvan.models import LichSuTuVan, LuatTuVan


class BaoCaoView(QuanTriMixin, TemplateView):
    template_name = "baocao/bao_cao.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            form=LocThoiGianForm(),
            so_cay=CayTrong.objects.count(),
            so_luat=LuatTuVan.objects.filter(is_active=True).count(),
            so_lich_su=LichSuTuVan.objects.count(),
        )
        return ctx


class _XuatExcelView(QuanTriMixin, View):
    """Lớp cơ sở: lớp con khai báo ten_bao_cao, tien_to_tep và tao_sheet(request) -> list sheet (hoặc None nếu bộ lọc sai)."""

    ten_bao_cao = ""
    tien_to_tep = ""

    def tao_sheet(self, request):
        raise NotImplementedError

    def get(self, request):
        cac_sheet = self.tao_sheet(request)
        if cac_sheet is None:  # bộ lọc không hợp lệ: không xuất file
            messages.error(request, "Khoảng ngày không hợp lệ. Vui lòng chọn lại.")
            return redirect("baocao:bao_cao")
        noi_dung, so_dong = tao_xlsx(cac_sheet)
        NhatKy.ghi(request.user, "Xuất báo cáo", f"BaoCao: {self.ten_bao_cao}", f"{so_dong} dòng")
        return phan_hoi_xlsx(noi_dung, ten_tep(self.tien_to_tep))


class CayTrongXuatView(_XuatExcelView):
    ten_bao_cao, tien_to_tep = "cay-trong", "cay-trong"

    def tao_sheet(self, request):
        return [services.sheet_cay_trong()]


class LuatXuatView(_XuatExcelView):
    ten_bao_cao, tien_to_tep = "luat-tu-van", "luat-tu-van-hien-hanh"

    def tao_sheet(self, request):
        return [services.sheet_luat_hien_hanh()]


class LichSuXuatView(_XuatExcelView):
    ten_bao_cao, tien_to_tep = "lich-su-tu-van", "lich-su-tu-van"

    def tao_sheet(self, request):
        form = LocThoiGianForm(request.GET)
        if not form.is_valid():
            return None
        return [services.sheet_lich_su_tu_van(form.cleaned_data["tu_ngay"], form.cleaned_data["den_ngay"])]
