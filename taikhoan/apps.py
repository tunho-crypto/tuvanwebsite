from django.apps import AppConfig


class TaikhoanConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "taikhoan"

    def ready(self):
        from taikhoan import signals  # noqa: F401  (đăng ký signal ghi nhật ký)
