from django import forms

from taikhoan.forms import BootstrapMixin
from tuvan.services import chuan_hoa_van_ban


class CauHoiForm(BootstrapMixin, forms.Form):
    noi_dung = forms.CharField(
        label="Câu hỏi của bạn",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Ví dụ: Làm thế nào để tưới nước tiết kiệm cho cà phê mùa khô?"}),
    )

    def clean_noi_dung(self):
        noi_dung = self.cleaned_data["noi_dung"].strip()
        if len(chuan_hoa_van_ban(noi_dung)) < 5:
            raise forms.ValidationError("Câu hỏi quá ngắn, vui lòng mô tả rõ hơn (ít nhất 5 ký tự).")
        return noi_dung


class TraLoiForm(BootstrapMixin, forms.Form):
    noi_dung = forms.CharField(label="Nội dung trả lời", max_length=3000, widget=forms.Textarea(attrs={"rows": 6}))

    def clean_noi_dung(self):
        noi_dung = self.cleaned_data["noi_dung"].strip()
        if not noi_dung:
            raise forms.ValidationError("Vui lòng nhập nội dung trả lời.")
        return noi_dung
