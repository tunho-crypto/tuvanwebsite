"""Truy xuất nguồn gốc (quy tắc 10): kết quả tư vấn -> LuatTuVan -> TaiLieu.

Đường dẫn: /truy-xuat/?ma=<mã luật>[&ls=<mã lịch sử tư vấn>]. Có `ls` thì hiển thị thêm ngữ cảnh lần tư vấn,
và nếu luật đã bị xóa thì vẫn truy xuất được nguồn từ bản chụp lưu trong lịch sử (chỉ khi người dùng được xem lịch sử đó).
"""
from django.views.generic import TemplateView

from taikhoan.models import VaiTro
from taikhoan.permissions import VaiTroRequiredMixin
from tuvan.models import LichSuTuVan, LuatTuVan
from tuvan.views import VAI_TRO_XEM_TAT_CA


class TruyXuatView(VaiTroRequiredMixin, TemplateView):
    template_name = "truyxuat/truy_xuat.html"

    def lich_su_xem_duoc(self, ma_lstv):
        if not ma_lstv:
            return None
        qs = LichSuTuVan.objects.all()
        if not self.request.user.co_vai_tro(*VAI_TRO_XEM_TAT_CA):
            qs = qs.filter(nguoi_dung=self.request.user)  # không lộ lịch sử của người khác
        return qs.filter(ma_lstv=ma_lstv).first()

    def get(self, request, *args, **kwargs):
        ma = request.GET.get("ma", "").strip()
        ctx = self.get_context_data(ma=ma)
        if not ma:
            return self.render_to_response(ctx)

        luat = LuatTuVan.objects.select_related("cay_tro", "tinh_thanh", "mua_vu", "tai_lieu").filter(rule_id=ma).first()
        lich_su = self.lich_su_xem_duoc(request.GET.get("ls", "").strip())
        ban_chup = None
        if lich_su:
            ban_chup = next((dx for dx in lich_su.ket_qua_json.get("de_xuat", []) if dx.get("rule_id") == ma), None)

        ctx.update(
            luat=luat,
            lich_su=lich_su,
            ban_chup=ban_chup,
            la_quan_ly=request.user.co_vai_tro(VaiTro.ADMIN, VaiTro.BIEN_TAP),
        )
        if luat and ban_chup:
            tl_hien_tai = luat.tai_lieu.ma_tl if luat.tai_lieu else None
            tl_luc_tu_van = (ban_chup.get("tai_lieu") or {}).get("ma_tl")
            ctx["tai_lieu_da_doi"] = tl_hien_tai != tl_luc_tu_van
        if luat is None and ban_chup is None:
            ctx["khong_tim_thay"] = True
            return self.render_to_response(ctx, status=404)
        return self.render_to_response(ctx)
