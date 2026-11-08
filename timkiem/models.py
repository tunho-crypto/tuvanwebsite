from django.db import models
from django.utils import timezone


class LichSuTimKiem(models.Model):
    ma_ls = models.CharField("Mã lịch sử", max_length=30, unique=True)
    tu_khoa = models.CharField("Từ khóa", max_length=255)
    thoi_gian = models.DateTimeField("Thời gian", default=timezone.now, db_index=True)
    lich_su_tu_van = models.ForeignKey(
        "tuvan.LichSuTuVan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lich_su_tim_kiem",
        verbose_name="Lịch sử tư vấn",
    )
    cau_hoi = models.ForeignKey(
        "hoidap.CauHoi",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lich_su_tim_kiem",
        verbose_name="Câu hỏi",
    )

    class Meta:
        verbose_name = "Lịch sử tìm kiếm"
        verbose_name_plural = "Lịch sử tìm kiếm"
        ordering = ["-thoi_gian", "-id"]

    def __str__(self):
        return self.tu_khoa
