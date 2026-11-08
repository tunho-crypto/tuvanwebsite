import re

from django import forms
from django.core.validators import MinValueValidator, URLValidator

from danhmuc.models import MuaVu, TinhThanh
from taikhoan.forms import BootstrapMixin
from tuvan.models import LuatTuVan
from tuvan.services import chuan_hoa_van_ban


class TuVanForm(BootstrapMixin, forms.Form):
    """Đầu vào tư vấn. Tỉnh và mùa gửi lên bằng MÃ (ma_tinh, ma_mua) để dùng chung với API và đường dẫn điền sẵn."""

    nhu_cau = forms.CharField(
        label="Nhu cầu",
        max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Ví dụ: Cây giá trị kinh tế cao"}),
    )
    tinh_thanh = forms.ModelChoiceField(
        label="Tỉnh thành", queryset=TinhThanh.objects.order_by("ten_tinh"), to_field_name="ma_tinh", empty_label="-- Chọn tỉnh --"
    )
    mua_vu = forms.ModelChoiceField(
        label="Mùa vụ",
        queryset=MuaVu.objects.order_by("id"),
        to_field_name="ma_mua",
        required=False,
        empty_label="-- Không chọn mùa --",
    )

    def clean_nhu_cau(self):
        nhu_cau = self.cleaned_data["nhu_cau"].strip()
        if not chuan_hoa_van_ban(nhu_cau):
            raise forms.ValidationError("Vui lòng nhập nhu cầu.")
        return nhu_cau


class LuatTuVanForm(BootstrapMixin, forms.ModelForm):
    """Thêm/sửa luật. Mã luật tự sinh khi tạo (không nhập); từ khóa lưu vào condition_json['tu_khoa']."""

    tu_khoa = forms.CharField(
        label="Từ khóa nhu cầu",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Mỗi dòng một cụm từ khóa, ví dụ: giá trị cao. Cụm khớp khi mọi từ của cụm có trong nhu cầu (không phân biệt dấu).",
    )
    duong_dan_tham_khao = forms.URLField(
        label="Liên kết tham khảo trực tiếp",
        required=False,
        max_length=500,
        validators=[URLValidator(schemes=["http", "https"])],
        help_text="Không bắt buộc. Nhập URL http:// hoặc https://; sẽ hiển thị trong luật và kết quả tư vấn.",
    )

    class Meta:
        model = LuatTuVan
        fields = [
            "cay_tro", "tinh_thanh", "mua_vu", "ky_thuat", "tu_khoa", "duong_dan_tham_khao",
            "score_weight", "tai_lieu", "is_active",
        ]
        localized_fields = ["score_weight"]  # hiển thị 1,00 và chấp nhận cả 1,5 lẫn 1.5
        help_texts = {
            "score_weight": "Chỉ dùng để xếp thứ hạng khi hai đề xuất bằng điểm.",
            "tinh_thanh": "Để trống nếu luật áp dụng cho mọi tỉnh.",
            "mua_vu": "Để trống nếu luật áp dụng cho mọi mùa.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tinh_thanh"].empty_label = "-- Mọi tỉnh (luật chung) --"
        self.fields["mua_vu"].empty_label = "-- Mọi mùa (luật chung) --"
        self.fields["ky_thuat"].empty_label = "-- Chưa gắn kỹ thuật --"
        self.fields["tai_lieu"].empty_label = "-- Chưa có tài liệu --"
        self.fields["score_weight"].validators.append(MinValueValidator(0))
        if self.instance.pk:
            self.initial["tu_khoa"] = "\n".join((self.instance.condition_json or {}).get("tu_khoa", []))

    def clean_tu_khoa(self):
        da_thay, ket_qua = set(), []
        for cum in re.split(r"[\n;,]+", self.cleaned_data["tu_khoa"]):
            cum = " ".join(cum.split())
            khoa = chuan_hoa_van_ban(cum)
            if not khoa or khoa in da_thay:
                continue
            if len(cum) > 100:
                raise forms.ValidationError("Mỗi cụm từ khóa tối đa 100 ký tự.")
            da_thay.add(khoa)
            ket_qua.append(cum)
        if not ket_qua:
            raise forms.ValidationError("Nhập ít nhất một cụm từ khóa.")
        return ket_qua
