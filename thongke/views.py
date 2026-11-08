from urllib.parse import urlencode

from django.views.generic import TemplateView

from baocao.excel import phan_hoi_xlsx, ten_tep, tao_xlsx
from taikhoan.models import NhatKy
from taikhoan.permissions import QuanTriMixin
from thongke import services
from thongke.forms import LocThoiGianForm
from thongke.xuat import cac_sheet_thong_ke


class ThongKeView(QuanTriMixin, TemplateView):
    """Thống kê (chỉ ADMIN). `?xuat=xlsx` tải file Excel của đúng bộ lọc đang xem."""

    template_name = "thongke/thong_ke.html"

    def get(self, request, *args, **kwargs):
        form = LocThoiGianForm(request.GET)
        ctx = self.get_context_data(form=form)
        if form.is_valid():
            tu_ngay, den_ngay = form.cleaned_data["tu_ngay"], form.cleaned_data["den_ngay"]
            tk = services.thong_ke(tu_ngay, den_ngay)
            if request.GET.get("xuat") == "xlsx":
                noi_dung, so_dong = tao_xlsx(cac_sheet_thong_ke(tk))
                NhatKy.ghi(request.user, "Xuất báo cáo", "BaoCao: thong-ke", f"{so_dong} dòng")
                return phan_hoi_xlsx(noi_dung, ten_tep("thong-ke"))
            loc = {k: v.isoformat() for k, v in (("tu_ngay", tu_ngay), ("den_ngay", den_ngay)) if v}
            ctx.update(tk=tk, query_xuat=urlencode({**loc, "xuat": "xlsx"}))
        return self.render_to_response(ctx)  # bộ lọc sai: hiện lỗi, không tính, không xuất file
