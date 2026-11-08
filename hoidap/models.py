from django.conf import settings
from django.db import models
from django.utils import timezone


class CauHoi(models.Model):
    CHO_TRA_LOI = "CHO_TRA_LOI"
    DA_TRA_LOI = "DA_TRA_LOI"
    NGOAI_PHAM_VI = "NGOAI_PHAM_VI"
    DONG = "DONG"
    TRANG_THAI_CHOICES = [
        (CHO_TRA_LOI, "Chờ trả lời"),
        (DA_TRA_LOI, "Đã trả lời"),
        (NGOAI_PHAM_VI, "Ngoài phạm vi"),
        (DONG, "Đã đóng"),
    ]

    ma_ch = models.CharField("Mã câu hỏi", max_length=30, unique=True)
    nguoi_dung = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cau_hoi", verbose_name="Người hỏi"
    )
    noi_dung = models.TextField("Nội dung")
    trang_thai = models.CharField("Trạng thái", max_length=20, choices=TRANG_THAI_CHOICES, default=CHO_TRA_LOI)
    # Thêm so với mục 4: hiển thị ngày hỏi và để thống kê theo thời gian ở tuần 5
    thoi_gian = models.DateTimeField("Thời gian", default=timezone.now, editable=False, db_index=True)

    class Meta:
        verbose_name = "Câu hỏi"
        verbose_name_plural = "Câu hỏi"
        ordering = ["-id"]

    def __str__(self):
        return self.ma_ch


class TraLoi(models.Model):
    """Câu trả lời của chuyên gia, hoặc câu trả lời tiêu chuẩn tự động khi câu hỏi ngoài phạm vi (la_tu_dong=True).
    Mỗi câu hỏi chỉ có một câu trả lời (OneToOne) nên hai chuyên gia không thể cùng trả lời một câu."""

    cau_hoi = models.OneToOneField(CauHoi, on_delete=models.CASCADE, related_name="tra_loi", verbose_name="Câu hỏi")
    nguoi_tra_loi = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tra_loi",
        verbose_name="Người trả lời",
    )
    noi_dung = models.TextField("Nội dung")
    la_tu_dong = models.BooleanField("Trả lời tự động", default=False)
    thoi_gian = models.DateTimeField("Thời gian", default=timezone.now, editable=False)

    class Meta:
        verbose_name = "Trả lời"
        verbose_name_plural = "Trả lời"

    def __str__(self):
        return f"Trả lời {self.cau_hoi.ma_ch}"
