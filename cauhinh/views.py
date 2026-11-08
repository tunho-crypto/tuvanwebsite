from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from cauhinh import services
from cauhinh.forms import TrongSoForm
from taikhoan.permissions import QuanTriMixin
from taikhoan.templatetags.dinh_dang import so
from tuvan.services import TrongSoKhongHopLe, lay_trong_so


class TrongSoView(QuanTriMixin, FormView):
    """Cấu hình trọng số w1, w2, w3 (chỉ ADMIN)."""

    form_class = TrongSoForm
    template_name = "form_chung.html"
    extra_context = {
        "tieu_de": "Cấu hình trọng số tư vấn",
        "ghi_chu": "Điểm phù hợp = w1 × khớp nhu cầu + w2 × khớp tỉnh thành + w3 × khớp mùa vụ. Ba trọng số không âm và có tổng bằng 1.",
        "url_huy": reverse_lazy("trang_chu"),
    }

    def get_initial(self):
        try:
            return {k: so(v) for k, v in lay_trong_so().items()}
        except TrongSoKhongHopLe:
            return {}  # cấu hình đang hỏng: để trống cho ADMIN nhập lại

    def form_valid(self, form):
        d = form.cleaned_data
        try:
            services.cap_nhat_trong_so(self.request.user, d["w1"], d["w2"], d["w3"])
        except TrongSoKhongHopLe as loi:
            form.add_error(None, str(loi))
            return self.form_invalid(form)
        messages.success(self.request, "Đã cập nhật trọng số.")
        return redirect("cauhinh:trong_so")
