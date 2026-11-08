"""CRUD 5 bảng danh mục bằng MỘT bộ view cấu hình (CAU_HINH_DANH_MUC).

Xem: mọi người dùng đã đăng nhập. Thêm/sửa/xóa: ADMIN và BIEN_TAP.
"""
from urllib.parse import urlsplit

from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, ListView, TemplateView

from danhmuc import services
from danhmuc.forms import tao_form_danh_muc
from danhmuc.models import CayTrong, KyThuat, MuaVu, TaiLieu, TinhThanh
from taikhoan.models import VaiTro
from taikhoan.permissions import VaiTroRequiredMixin
from taikhoan.services import NghiepVuError
from taikhoan.views import PhanTrangMixin

VAI_TRO_SUA = (VaiTro.ADMIN, VaiTro.BIEN_TAP)

# slug trong URL -> cấu hình. cot: các cột hiển thị; tim: các cột tìm kiếm theo từ khóa.
CAU_HINH_DANH_MUC = {
    "cay-trong": {
        "model": CayTrong, "ten": "Cây trồng", "truong_ma": "ma_cay",
        "fields": ["ma_cay", "ten_cay", "nhom_cay", "dac_diem", "hinh_anh"],
        "cot": ["ma_cay", "ten_cay", "nhom_cay"], "tim": ["ma_cay", "ten_cay"],
        "cot_anh": True,
    },
    "tinh-thanh": {
        "model": TinhThanh, "ten": "Tỉnh thành", "truong_ma": "ma_tinh",
        "fields": ["ma_tinh", "ten_tinh", "vung_mien"],
        "cot": ["ma_tinh", "ten_tinh", "vung_mien"], "tim": ["ma_tinh", "ten_tinh"],
    },
    "mua-vu": {
        "model": MuaVu, "ten": "Mùa vụ", "truong_ma": "ma_mua",
        "fields": ["ma_mua", "ten_mua", "thoi_gian_tu", "thoi_gian_den"],
        "cot": ["ma_mua", "ten_mua", "thoi_gian_tu", "thoi_gian_den"], "tim": ["ma_mua", "ten_mua"],
    },
    "ky-thuat": {
        "model": KyThuat, "ten": "Kỹ thuật", "truong_ma": "ma_kt",
        "fields": ["ma_kt", "ten_kt", "loai_kt", "noi_dung", "hinh_anh"],
        "cot": ["ma_kt", "ten_kt", "loai_kt"], "tim": ["ma_kt", "ten_kt", "loai_kt"],
        "cot_anh": True,
    },
    "tai-lieu": {
        "model": TaiLieu, "ten": "Tài liệu", "truong_ma": "ma_tl",
        "fields": ["ma_tl", "ten_tl", "nguon_tham_chieu", "duong_dan"],
        "cot": ["ma_tl", "ten_tl", "nguon_tham_chieu", "duong_dan"],
        "tim": ["ma_tl", "ten_tl", "nguon_tham_chieu"],
        "cot_lien_ket": "duong_dan",
    },
}


class DanhMucMixin(VaiTroRequiredMixin):
    """Tra cấu hình theo kwargs['muc']; slug lạ thì 404 (sau khi đã kiểm tra quyền)."""

    def dispatch(self, request, *args, **kwargs):
        self.muc = kwargs["muc"]
        if self.muc not in CAU_HINH_DANH_MUC:
            if request.user.is_authenticated:
                raise Http404("Không có danh mục này")
        self.cau_hinh = CAU_HINH_DANH_MUC.get(self.muc)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            muc=self.muc, ten_danh_muc=self.cau_hinh["ten"], url_ds=reverse("danhmuc:ds", kwargs={"muc": self.muc}),
            co_quyen_sua=self.request.user.co_vai_tro(*VAI_TRO_SUA),
        )
        return ctx

    def lay_doi_tuong(self):
        try:
            return self.cau_hinh["model"].objects.get(pk=self.kwargs["pk"])
        except self.cau_hinh["model"].DoesNotExist:
            raise Http404("Không tìm thấy bản ghi")


def _gia_tri_hien_thi(doi_tuong, ten_truong):
    truong = doi_tuong._meta.get_field(ten_truong)
    return getattr(doi_tuong, f"get_{ten_truong}_display")() if truong.choices else getattr(doi_tuong, ten_truong)


def _lien_ket_http_an_toan(gia_tri):
    try:
        parsed = urlsplit(gia_tri or "")
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class DanhMucDanhSachView(DanhMucMixin, PhanTrangMixin, ListView):
    template_name = "danhmuc/danh_sach.html"
    paginate_by = 10

    def get_queryset(self):
        qs = self.cau_hinh["model"].objects.all()
        q = self.request.GET.get("q", "").strip()
        if q:
            dieu_kien = Q()
            for truong in self.cau_hinh["tim"]:
                dieu_kien |= Q(**{f"{truong}__icontains": q})
            qs = qs.filter(dieu_kien)
        return qs.order_by(self.cau_hinh["truong_ma"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = self.cau_hinh["model"]
        ctx["tieu_de_cot"] = [model._meta.get_field(t).verbose_name for t in self.cau_hinh["cot"]]
        if self.cau_hinh.get("cot_anh"):
            ctx["tieu_de_cot"].append("Hình ảnh")
        ctx["cot_lien_ket"] = self.cau_hinh.get("cot_lien_ket")
        ctx["link_column_index"] = (
            self.cau_hinh["cot"].index(ctx["cot_lien_ket"]) if ctx["cot_lien_ket"] else -1
        )
        ctx["co_cot_anh"] = bool(self.cau_hinh.get("cot_anh"))
        ctx["dong"] = [
            {
                "pk": o.pk,
                "o": [_gia_tri_hien_thi(o, t) for t in self.cau_hinh["cot"]],
                "ten": str(o),
                "anh": o.hinh_anh.url if self.cau_hinh.get("cot_anh") and o.hinh_anh else "",
                "lien_ket_an_toan": (
                    _lien_ket_http_an_toan(getattr(o, ctx["cot_lien_ket"]))
                    if ctx["cot_lien_ket"]
                    else False
                ),
            }
            for o in ctx["page_obj"]
        ]
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class _DanhMucFormView(DanhMucMixin, FormView):
    template_name = "form_chung.html"
    vai_tro_cho_phep = VAI_TRO_SUA
    doi_tuong = None

    def get_form_class(self):
        return tao_form_danh_muc(self.cau_hinh)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.doi_tuong
        if self.request.method == "POST":
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["url_huy"] = ctx["url_ds"]
        return ctx

    def form_valid(self, form):
        doi_tuong = services.luu_danh_muc(self.request.user, form, self.cau_hinh["truong_ma"])
        messages.success(self.request, f"Đã lưu {self.cau_hinh['ten'].lower()} «{doi_tuong}».")
        return redirect("danhmuc:ds", muc=self.muc)


class DanhMucThemView(_DanhMucFormView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tieu_de"] = f"Thêm {self.cau_hinh['ten'].lower()}"
        return ctx


class DanhMucSuaView(_DanhMucFormView):
    def dispatch(self, request, *args, **kwargs):
        self.muc = kwargs["muc"]
        if request.user.is_authenticated and request.user.co_vai_tro(*VAI_TRO_SUA) and self.muc in CAU_HINH_DANH_MUC:
            self.cau_hinh = CAU_HINH_DANH_MUC[self.muc]
            self.kwargs = kwargs
            self.doi_tuong = self.lay_doi_tuong()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tieu_de"] = f"Sửa {self.cau_hinh['ten'].lower()}: {self.doi_tuong}"
        return ctx


class DanhMucXoaView(DanhMucMixin, TemplateView):
    """GET: trang xác nhận. POST: xóa; bị chặn thì báo lỗi và quay về danh sách."""

    template_name = "danhmuc/xac_nhan_xoa.html"
    vai_tro_cho_phep = VAI_TRO_SUA

    def dispatch(self, request, *args, **kwargs):
        self.muc = kwargs["muc"]
        if request.user.is_authenticated and request.user.co_vai_tro(*VAI_TRO_SUA) and self.muc in CAU_HINH_DANH_MUC:
            self.cau_hinh = CAU_HINH_DANH_MUC[self.muc]
            self.kwargs = kwargs
            self.doi_tuong = self.lay_doi_tuong()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["doi_tuong"] = self.doi_tuong
        return ctx

    def post(self, request, *args, **kwargs):
        try:
            services.xoa_danh_muc(request.user, self.doi_tuong, self.cau_hinh["truong_ma"])
        except NghiepVuError as loi:
            messages.error(request, str(loi))
        else:
            messages.success(request, f"Đã xóa {self.cau_hinh['ten'].lower()} «{self.doi_tuong}».")
        return redirect("danhmuc:ds", muc=self.muc)
