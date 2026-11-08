"""Các bảng danh mục: cây trồng, tỉnh thành, mùa vụ, kỹ thuật, tài liệu."""
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def validate_image_size(image):
    max_size = 5 * 1024 * 1024
    if image.size > max_size:
        raise ValidationError("Ảnh không được vượt quá 5 MB.")


class CayTrong(models.Model):
    CONG_NGHIEP = "CONG_NGHIEP"
    AN_QUA = "AN_QUA"
    NGAN_NGAY = "NGAN_NGAY"
    NHOM_CAY_CHOICES = [
        (CONG_NGHIEP, "Cây công nghiệp"),
        (AN_QUA, "Cây ăn quả"),
        (NGAN_NGAY, "Cây ngắn ngày"),
    ]

    ma_cay = models.CharField("Mã cây", max_length=30, unique=True)
    ten_cay = models.CharField("Tên cây", max_length=150)
    nhom_cay = models.CharField("Nhóm cây", max_length=20, choices=NHOM_CAY_CHOICES)
    dac_diem = models.TextField("Đặc điểm", blank=True)
    hinh_anh = models.ImageField(
        "Hình ảnh",
        upload_to="cay_trong/",
        blank=True,
        validators=[validate_image_size],
    )

    class Meta:
        verbose_name = "Cây trồng"
        verbose_name_plural = "Cây trồng"
        ordering = ["ten_cay"]

    def __str__(self):
        return self.ten_cay


class TinhThanh(models.Model):
    ma_tinh = models.CharField("Mã tỉnh", max_length=30, unique=True)
    ten_tinh = models.CharField("Tên tỉnh", max_length=100)
    vung_mien = models.CharField("Vùng miền", max_length=100, default="Tây Nguyên")

    class Meta:
        verbose_name = "Tỉnh thành"
        verbose_name_plural = "Tỉnh thành"
        ordering = ["ten_tinh"]

    def __str__(self):
        return self.ten_tinh


class MuaVu(models.Model):
    """Mùa vụ lặp lại hằng năm: lưu tháng bắt đầu và tháng kết thúc (1-12)."""

    ma_mua = models.CharField("Mã mùa", max_length=30, unique=True)
    ten_mua = models.CharField("Tên mùa", max_length=100)
    thoi_gian_tu = models.PositiveSmallIntegerField(
        "Từ tháng", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    thoi_gian_den = models.PositiveSmallIntegerField(
        "Đến tháng", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    class Meta:
        verbose_name = "Mùa vụ"
        verbose_name_plural = "Mùa vụ"
        ordering = ["id"]

    def __str__(self):
        return self.ten_mua


class KyThuat(models.Model):
    ma_kt = models.CharField("Mã kỹ thuật", max_length=30, unique=True)
    ten_kt = models.CharField("Tên kỹ thuật", max_length=200)
    loai_kt = models.CharField("Loại kỹ thuật", max_length=100)
    noi_dung = models.TextField("Nội dung", blank=True)
    hinh_anh = models.ImageField(
        "Hình ảnh",
        upload_to="ky_thuat/",
        blank=True,
        validators=[validate_image_size],
    )

    class Meta:
        verbose_name = "Kỹ thuật"
        verbose_name_plural = "Kỹ thuật"
        ordering = ["ten_kt"]

    def __str__(self):
        return self.ten_kt


class TaiLieu(models.Model):
    """Tài liệu tham chiếu (WASI, Sở Nông nghiệp...) dùng cho truy xuất nguồn gốc."""

    ma_tl = models.CharField("Mã tài liệu", max_length=30, unique=True)
    ten_tl = models.CharField("Tên tài liệu", max_length=255)
    nguon_tham_chieu = models.CharField("Nguồn tham chiếu", max_length=255)
    duong_dan = models.CharField("Đường dẫn", max_length=500, blank=True)

    class Meta:
        verbose_name = "Tài liệu"
        verbose_name_plural = "Tài liệu"
        ordering = ["ten_tl"]

    def __str__(self):
        return self.ten_tl
