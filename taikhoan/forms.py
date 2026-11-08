"""Form tài khoản. BootstrapMixin gắn class Bootstrap 5 cho mọi widget."""
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm
from django.core.exceptions import ValidationError

from taikhoan.models import NguoiDung, VaiTro


class BootstrapMixin:
    """Gắn class form-control / form-select / form-check-input và is-invalid khi có lỗi."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for truong in self.fields.values():
            lop = self._lop_bootstrap(truong.widget)
            self._them_lop(truong.widget, lop)

    @staticmethod
    def _lop_bootstrap(widget):
        if isinstance(widget, forms.CheckboxInput):
            return "form-check-input"
        if isinstance(widget, (forms.Select, forms.SelectMultiple)):
            return "form-select"
        return "form-control"

    @staticmethod
    def _them_lop(widget, lop):
        cac_lop = widget.attrs.get("class", "").split()
        if lop not in cac_lop:
            widget.attrs["class"] = " ".join(cac_lop + [lop])

    def full_clean(self):
        super().full_clean()
        for ten in self.errors:
            if ten in self.fields:
                self._them_lop(self.fields[ten].widget, "is-invalid")


class DangNhapForm(BootstrapMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Tên đăng nhập hoặc mật khẩu không đúng.",
        "inactive": "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Tên đăng nhập"
        self.fields["password"].label = "Mật khẩu"

    def clean(self):
        try:
            return super().clean()
        except ValidationError:
            # Báo riêng khi mật khẩu đúng nhưng tài khoản đã bị khóa
            username = self.cleaned_data.get("username")
            password = self.cleaned_data.get("password")
            nguoi_dung = NguoiDung.objects.filter(username=username).first() if username else None
            if nguoi_dung and not nguoi_dung.is_active and nguoi_dung.check_password(password or ""):
                raise ValidationError(self.error_messages["inactive"], code="inactive")
            raise


class DangKyForm(BootstrapMixin, forms.Form):
    username = forms.CharField(
        label="Tên đăng nhập",
        max_length=150,
        validators=NguoiDung._meta.get_field("username").validators,
    )
    ho = forms.CharField(label="Họ", max_length=150)
    ten = forms.CharField(label="Tên", max_length=150)
    email = forms.EmailField(label="Email")
    mat_khau = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput(render_value=False))
    nhap_lai_mat_khau = forms.CharField(label="Nhập lại mật khẩu", widget=forms.PasswordInput(render_value=False))

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if NguoiDung.objects.filter(username__iexact=username).exists():
            raise ValidationError("Tên đăng nhập đã tồn tại.")
        return username

    def clean(self):
        du_lieu = super().clean()
        mat_khau = du_lieu.get("mat_khau")
        nhap_lai = du_lieu.get("nhap_lai_mat_khau")
        if mat_khau and nhap_lai and mat_khau != nhap_lai:
            self.add_error("nhap_lai_mat_khau", "Hai mật khẩu không khớp.")
        if mat_khau:
            nguoi_dung = NguoiDung(
                username=du_lieu.get("username", ""),
                first_name=du_lieu.get("ten", ""),
                last_name=du_lieu.get("ho", ""),
                email=du_lieu.get("email", ""),
            )
            try:
                password_validation.validate_password(mat_khau, user=nguoi_dung)
            except ValidationError as loi:
                self.add_error("mat_khau", loi)
        return du_lieu


class DoiMatKhauForm(BootstrapMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Mật khẩu hiện tại"
        self.fields["new_password1"].label = "Mật khẩu mới"
        self.fields["new_password2"].label = "Nhập lại mật khẩu mới"


class KhoiPhucMatKhauForm(BootstrapMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Email đã đăng ký"


class XacNhanMaKhoiPhucForm(BootstrapMixin, forms.Form):
    email = forms.EmailField(label="Email đã đăng ký")
    ma_xac_minh = forms.RegexField(
        regex=r"^\d{6}$",
        label="Mã xác minh gồm 6 chữ số",
        error_messages={"invalid": "Mã xác minh phải gồm đúng 6 chữ số."},
    )
    mat_khau_moi = forms.CharField(label="Mật khẩu mới", widget=forms.PasswordInput(render_value=False))
    nhap_lai_mat_khau = forms.CharField(label="Nhập lại mật khẩu mới", widget=forms.PasswordInput(render_value=False))

    def clean_email(self):
        return self.cleaned_data["email"].strip()

    def clean(self):
        du_lieu = super().clean()
        mat_khau = du_lieu.get("mat_khau_moi")
        nhap_lai = du_lieu.get("nhap_lai_mat_khau")
        if mat_khau and nhap_lai and mat_khau != nhap_lai:
            self.add_error("nhap_lai_mat_khau", "Hai mật khẩu không khớp.")
        if mat_khau:
            try:
                password_validation.validate_password(mat_khau)
            except ValidationError as loi:
                self.add_error("mat_khau_moi", loi)
        return du_lieu


class _NguoiDungFormGoc(BootstrapMixin, forms.Form):
    """Form thường (không phải ModelForm) để service đọc được giá trị CŨ trong CSDL khi kiểm tra quy tắc."""

    ho = forms.CharField(label="Họ", max_length=150, required=False)
    ten = forms.CharField(label="Tên", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=False)
    vai_tro = forms.ModelChoiceField(label="Vai trò", queryset=VaiTro.objects.all(), empty_label=None)
    is_active = forms.BooleanField(label="Đang hoạt động (bỏ chọn để khóa)", required=False, initial=True)


class NguoiDungThemForm(_NguoiDungFormGoc):
    username = forms.CharField(label="Tên đăng nhập", max_length=150)
    mat_khau = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput(render_value=False))
    nhap_lai_mat_khau = forms.CharField(label="Nhập lại mật khẩu", widget=forms.PasswordInput(render_value=False))
    field_order = ["username", "ho", "ten", "email", "vai_tro", "mat_khau", "nhap_lai_mat_khau", "is_active"]

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if NguoiDung.objects.filter(username__iexact=username).exists():
            raise ValidationError("Tên đăng nhập đã tồn tại.")
        return username

    def clean(self):
        du_lieu = super().clean()
        mk, nhap_lai = du_lieu.get("mat_khau"), du_lieu.get("nhap_lai_mat_khau")
        if mk and nhap_lai and mk != nhap_lai:
            self.add_error("nhap_lai_mat_khau", "Hai mật khẩu không khớp.")
        elif mk:
            # Truyền một người dùng tạm (chưa lưu) để validator «giống thông tin cá nhân» thật sự có tác dụng
            nguoi_dung_tam = NguoiDung(
                username=du_lieu.get("username", ""), first_name=du_lieu.get("ten", ""),
                last_name=du_lieu.get("ho", ""), email=du_lieu.get("email", ""),
            )
            try:
                password_validation.validate_password(mk, user=nguoi_dung_tam)
            except ValidationError as loi:
                self.add_error("mat_khau", loi)
        return du_lieu


class NguoiDungSuaForm(_NguoiDungFormGoc):
    mat_khau_moi = forms.CharField(
        label="Mật khẩu mới",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Để trống nếu không đổi mật khẩu.",
    )

    def __init__(self, *args, nguoi_dung=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.nguoi_dung = nguoi_dung  # để validator «giống thông tin cá nhân» có tác dụng

    def clean_mat_khau_moi(self):
        mk = self.cleaned_data.get("mat_khau_moi")
        if mk:
            password_validation.validate_password(mk, user=self.nguoi_dung)  # ném ValidationError nếu yếu
        return mk
