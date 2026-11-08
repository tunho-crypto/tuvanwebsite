from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from taikhoan.forms import BootstrapMixin
from tuvan.services import TrongSoKhongHopLe, doc_so_thap_phan, kiem_tra_trong_so


class TrongSoForm(BootstrapMixin, forms.Form):
    """Nhập trọng số; chấp nhận cả dấu phẩy (0,5) lẫn dấu chấm (0.5)."""

    w1 = forms.CharField(label="w1 - Trọng số nhu cầu", max_length=10)
    w2 = forms.CharField(label="w2 - Trọng số tỉnh thành", max_length=10)
    w3 = forms.CharField(label="w3 - Trọng số mùa vụ", max_length=10)

    def _doc_so(self, ten):
        try:
            return doc_so_thap_phan(self.cleaned_data[ten])
        except TrongSoKhongHopLe as loi:
            raise ValidationError("Phải là số, ví dụ 0,5.") from loi

    def clean_w1(self):
        return self._doc_so("w1")

    def clean_w2(self):
        return self._doc_so("w2")

    def clean_w3(self):
        return self._doc_so("w3")

    def clean(self):
        du_lieu = super().clean()
        if all(isinstance(du_lieu.get(k), Decimal) for k in ("w1", "w2", "w3")):
            try:
                kiem_tra_trong_so({k: du_lieu[k] for k in ("w1", "w2", "w3")})
            except TrongSoKhongHopLe as loi:
                raise ValidationError(str(loi)) from loi
        return du_lieu
