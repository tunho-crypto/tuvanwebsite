"""Mô hình tài khoản: VaiTro, NguoiDung, NhatKy."""
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils import timezone


class VaiTro(models.Model):
    """Vai trò phân quyền: ADMIN, BIEN_TAP, CHUYEN_GIA, NONG_DAN."""

    ADMIN = "ADMIN"
    BIEN_TAP = "BIEN_TAP"
    CHUYEN_GIA = "CHUYEN_GIA"
    NONG_DAN = "NONG_DAN"

    ma_vai_tro = models.CharField("Mã vai trò", max_length=30, unique=True)
    ten_vai_tro = models.CharField("Tên vai trò", max_length=100)
    mo_ta = models.TextField("Mô tả", blank=True)

    class Meta:
        verbose_name = "Vai trò"
        verbose_name_plural = "Vai trò"
        ordering = ["id"]

    def __str__(self):
        return self.ten_vai_tro


class NguoiDungManager(UserManager):
    """Khi tạo superuser bằng `createsuperuser`, tự gán vai trò ADMIN (vì vai_tro bắt buộc)."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        if "vai_tro" not in extra_fields and "vai_tro_id" not in extra_fields:
            extra_fields["vai_tro"], _ = VaiTro.objects.get_or_create(
                ma_vai_tro=VaiTro.ADMIN, defaults={"ten_vai_tro": "Quản trị hệ thống"}
            )
        return super().create_superuser(username, email, password, **extra_fields)


class NguoiDung(AbstractUser):
    """Người dùng hệ thống: kế thừa AbstractUser, thêm vai trò."""

    vai_tro = models.ForeignKey(
        VaiTro, on_delete=models.PROTECT, related_name="nguoi_dung", verbose_name="Vai trò"
    )

    objects = NguoiDungManager()

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

    @property
    def ho_ten(self):
        """Họ tên theo kiểu Việt Nam (họ trước, tên sau); không có thì dùng username."""
        return f"{self.last_name} {self.first_name}".strip() or self.username

    def co_vai_tro(self, *ma):
        """True nếu người dùng có một trong các vai trò truyền vào. Ví dụ: u.co_vai_tro('ADMIN', 'BIEN_TAP')."""
        return self.vai_tro_id is not None and self.vai_tro.ma_vai_tro in ma

    def __str__(self):
        return self.ho_ten


class NhatKy(models.Model):
    """Nhật ký hành động quan trọng."""

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nhat_ky",
        verbose_name="Người dùng",
    )
    thoi_gian = models.DateTimeField("Thời gian", default=timezone.now, db_index=True)
    hanh_dong = models.CharField("Hành động", max_length=100)
    doi_tuong = models.CharField("Đối tượng", max_length=200, blank=True)
    chi_tiet = models.TextField("Chi tiết", blank=True)

    class Meta:
        verbose_name = "Nhật ký"
        verbose_name_plural = "Nhật ký"
        ordering = ["-thoi_gian", "-id"]

    @classmethod
    def ghi(cls, nguoi_dung, hanh_dong, doi_tuong="", chi_tiet=""):
        """Ghi một dòng nhật ký. `nguoi_dung` có thể là None hoặc AnonymousUser (lưu NULL)."""
        if nguoi_dung is not None and not getattr(nguoi_dung, "pk", None):
            nguoi_dung = None
        return cls.objects.create(
            nguoi_dung=nguoi_dung,
            hanh_dong=hanh_dong,
            doi_tuong=str(doi_tuong),
            chi_tiet=str(chi_tiet),
        )

    def __str__(self):
        return f"{self.thoi_gian:%d/%m/%Y %H:%M} - {self.hanh_dong}"


class MaKhoiPhucMatKhau(models.Model):
    """Mã khôi phục email đã băm, hết hạn sau thời gian ngắn và chỉ dùng một lần."""

    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ma_khoi_phuc_mat_khau",
        verbose_name="Người dùng",
    )
    ma_bam = models.CharField("Mã đã băm", max_length=128)
    tao_luc = models.DateTimeField("Thời gian tạo", default=timezone.now, db_index=True)
    het_han_luc = models.DateTimeField("Thời gian hết hạn", db_index=True)
    so_lan_thu = models.PositiveSmallIntegerField("Số lần nhập sai", default=0)
    da_su_dung_luc = models.DateTimeField("Thời gian sử dụng", null=True, blank=True)

    class Meta:
        verbose_name = "Mã khôi phục mật khẩu"
        verbose_name_plural = "Mã khôi phục mật khẩu"
        ordering = ["-tao_luc", "-id"]
        indexes = [models.Index(fields=["nguoi_dung", "tao_luc"])]
