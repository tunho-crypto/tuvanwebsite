"""Hỏi đáp: NONG_DAN đặt câu hỏi và xem của mình; CHUYEN_GIA trả lời; ADMIN xem tất cả (chỉ đọc)."""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView, ListView, TemplateView

from hoidap import services
from hoidap.forms import CauHoiForm, TraLoiForm
from hoidap.models import CauHoi
from taikhoan.models import VaiTro
from taikhoan.permissions import VaiTroRequiredMixin
from taikhoan.services import NghiepVuError
from taikhoan.views import PhanTrangMixin

VAI_TRO_XEM = (VaiTro.ADMIN, VaiTro.CHUYEN_GIA, VaiTro.NONG_DAN)
VAI_TRO_XEM_TAT_CA = (VaiTro.ADMIN, VaiTro.CHUYEN_GIA)


class _XemMixin(VaiTroRequiredMixin):
    vai_tro_cho_phep = VAI_TRO_XEM

    def lay_queryset(self):
        qs = CauHoi.objects.select_related("nguoi_dung", "tra_loi", "tra_loi__nguoi_tra_loi")
        if not self.request.user.co_vai_tro(*VAI_TRO_XEM_TAT_CA):  # NONG_DAN chỉ thấy câu hỏi của mình
            qs = qs.filter(nguoi_dung=self.request.user)
        return qs


class CauHoiDanhSachView(_XemMixin, PhanTrangMixin, ListView):
    template_name = "hoidap/ds.html"
    paginate_by = 10
    context_object_name = "ds_cau_hoi"

    def get_queryset(self):
        qs = self.lay_queryset()
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(ma_ch__icontains=q) | Q(noi_dung__icontains=q))
        trang_thai = self.request.GET.get("trang_thai", "")
        if trang_thai in dict(CauHoi.TRANG_THAI_CHOICES):
            qs = qs.filter(trang_thai=trang_thai)
        return qs.order_by("-thoi_gian", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["loc"] = {k: self.request.GET.get(k, "") for k in ("q", "trang_thai")}
        ctx["trang_thai_choices"] = CauHoi.TRANG_THAI_CHOICES
        ctx["xem_tat_ca"] = self.request.user.co_vai_tro(*VAI_TRO_XEM_TAT_CA)
        ctx["co_the_hoi"] = self.request.user.co_vai_tro(VaiTro.NONG_DAN)
        ctx["so_cho_tra_loi"] = self.lay_queryset().filter(trang_thai=CauHoi.CHO_TRA_LOI).count()
        return ctx


class CauHoiThemView(VaiTroRequiredMixin, FormView):
    vai_tro_cho_phep = (VaiTro.NONG_DAN,)
    form_class = CauHoiForm
    template_name = "form_chung.html"
    extra_context = {
        "tieu_de": "Đặt câu hỏi",
        "nut_luu": "Gửi câu hỏi",
        "ghi_chu": "Hãy nêu tên cây trồng hoặc kỹ thuật bạn quan tâm. Câu hỏi nằm ngoài phạm vi hỗ trợ sẽ được trả lời tự động.",
        "do_rong": 8,
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["url_huy"] = reverse("hoidap:ds")
        return ctx

    def form_valid(self, form):
        cau_hoi = services.gui_cau_hoi(self.request.user, form.cleaned_data["noi_dung"])
        if cau_hoi.trang_thai == CauHoi.NGOAI_PHAM_VI:
            messages.warning(self.request, "Câu hỏi nằm ngoài phạm vi hỗ trợ nên đã được trả lời tự động.")
        else:
            messages.success(self.request, f"Đã gửi câu hỏi {cau_hoi.ma_ch}. Chuyên gia sẽ trả lời sớm.")
        return redirect("hoidap:chi_tiet", pk=cau_hoi.pk)


class CauHoiChiTietView(_XemMixin, TemplateView):
    template_name = "hoidap/chi_tiet.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cau_hoi"] = get_object_or_404(self.lay_queryset(), pk=self.kwargs["pk"])  # của người khác -> 404
        ctx["co_the_tra_loi"] = self.request.user.co_vai_tro(VaiTro.CHUYEN_GIA) and ctx["cau_hoi"].trang_thai == CauHoi.CHO_TRA_LOI
        return ctx


class TraLoiView(VaiTroRequiredMixin, FormView):
    vai_tro_cho_phep = (VaiTro.CHUYEN_GIA,)
    form_class = TraLoiForm
    template_name = "form_chung.html"
    extra_context = {"nut_luu": "Gửi trả lời", "do_rong": 8}

    @cached_property
    def cau_hoi(self):  # chỉ tra cứu sau khi đã kiểm tra quyền
        return get_object_or_404(CauHoi.objects.select_related("nguoi_dung"), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        if self.cau_hoi.trang_thai != CauHoi.CHO_TRA_LOI:
            messages.error(request, "Câu hỏi này đã được xử lý, không thể trả lời nữa.")
            return redirect("hoidap:chi_tiet", pk=self.cau_hoi.pk)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tieu_de"] = f"Trả lời câu hỏi {self.cau_hoi.ma_ch}"
        ctx["ghi_chu"] = f"Câu hỏi của {self.cau_hoi.nguoi_dung.ho_ten}: {self.cau_hoi.noi_dung}"
        ctx["url_huy"] = reverse("hoidap:chi_tiet", args=[self.cau_hoi.pk])
        return ctx

    def form_valid(self, form):
        try:
            services.tra_loi_cau_hoi(self.request.user, self.cau_hoi, form.cleaned_data["noi_dung"])
        except NghiepVuError as loi:
            messages.error(self.request, str(loi))
        else:
            messages.success(self.request, f"Đã trả lời câu hỏi {self.cau_hoi.ma_ch}.")
        return redirect("hoidap:chi_tiet", pk=self.cau_hoi.pk)
