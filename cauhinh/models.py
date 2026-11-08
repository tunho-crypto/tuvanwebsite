from django.db import models


class CauHinhHeThong(models.Model):
    """Cặp tên - giá trị. Dùng lưu trọng số w1, w2, w3 của công thức tính điểm tư vấn."""

    ten_cau_hinh = models.CharField("Tên cấu hình", max_length=100, unique=True)
    gia_tri = models.CharField("Giá trị", max_length=255)

    class Meta:
        verbose_name = "Cấu hình hệ thống"
        verbose_name_plural = "Cấu hình hệ thống"
        ordering = ["ten_cau_hinh"]

    def __str__(self):
        return f"{self.ten_cau_hinh} = {self.gia_tri}"
