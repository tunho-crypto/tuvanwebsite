"""Form danh mục dựng tự động từ cấu hình; mã nghiệp vụ được cắt khoảng trắng, viết hoa TRƯỚC khi kiểm tra trùng."""
from django import forms
from django.core.validators import URLValidator
from django.forms import modelform_factory

from taikhoan.forms import BootstrapMixin


class DanhMucFormGoc(BootstrapMixin, forms.ModelForm):
    truong_ma = None  # lớp con do tao_form_danh_muc gán

    def clean(self):
        du_lieu = super().clean()
        ma = du_lieu.get(self.truong_ma)
        if ma:
            du_lieu[self.truong_ma] = ma.strip().upper()
        return du_lieu  # validate_unique (trong _post_clean) dùng giá trị đã chuẩn hóa này


def tao_form_danh_muc(cau_hinh):
    form = modelform_factory(cau_hinh["model"], form=DanhMucFormGoc, fields=cau_hinh["fields"])
    form.truong_ma = cau_hinh["truong_ma"]
    if "hinh_anh" in form.base_fields:
        form.base_fields["hinh_anh"].widget.attrs["accept"] = "image/*"
    if "duong_dan" in form.base_fields:
        form.base_fields["duong_dan"] = forms.URLField(
            label="Đường dẫn",
            required=False,
            max_length=500,
            validators=[URLValidator(schemes=["http", "https"])],
            help_text="Nhập liên kết tài liệu bắt đầu bằng http:// hoặc https://.",
        )
    return form
