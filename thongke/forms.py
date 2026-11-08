from django import forms

from taikhoan.forms import BootstrapMixin

DINH_DANG_NGAY = ["%Y-%m-%d", "%d/%m/%Y"]


class LocThoiGianForm(BootstrapMixin, forms.Form):
    """Lọc theo khoảng ngày (gồm cả hai đầu). Để trống nghĩa là không giới hạn."""

    tu_ngay = forms.DateField(
        label="Từ ngày", required=False, input_formats=DINH_DANG_NGAY, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )
    den_ngay = forms.DateField(
        label="Đến ngày", required=False, input_formats=DINH_DANG_NGAY, widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
    )

    def clean(self):
        du_lieu = super().clean()
        tu, den = du_lieu.get("tu_ngay"), du_lieu.get("den_ngay")
        if tu and den and tu > den:
            raise forms.ValidationError("«Từ ngày» phải trước hoặc bằng «Đến ngày».")
        return du_lieu
