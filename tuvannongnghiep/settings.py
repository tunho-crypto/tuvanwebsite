"""Cấu hình Django cho đồ án «Hệ thống tư vấn thông tin nông nghiệp Tây Nguyên»."""
import os
import sys
from pathlib import Path

from django.contrib.messages import constants as message_constants
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Đọc biến môi trường từ file .env (nếu có)
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "khoa-bi-mat-chi-dung-khi-phat-trien")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# KHÔNG dùng django.contrib.admin: toàn bộ giao diện tự xây bằng template Bootstrap
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # App của dự án
    "taikhoan",
    "danhmuc",
    "tuvan",
    "timkiem",
    "truyxuat",  # không có model: truy xuất nguồn gốc từ kết quả tư vấn
    "thongke",  # không có model: thống kê từ dữ liệu sẵn có
    "baocao",  # không có model: xuất Excel
    # Chỉ chứa model (đúng vị trí cuối cùng), giao diện làm ở tuần sau
    "hoidap",
    "cauhinh",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tuvannongnghiep.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "taikhoan.context_processors.menu",
                "taikhoan.context_processors.giao_dien",
            ],
        },
    },
]

WSGI_APPLICATION = "tuvannongnghiep.wsgi.application"

# PostgreSQL qua psycopg 3, cấu hình bằng biến môi trường
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "tuvannongnghiep_db"),
        "USER": os.getenv("DB_USER", "tuvan_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "taikhoan.NguoiDung"
LOGIN_URL = "/dang-nhap/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/dang-nhap/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "taikhoan.validators.MatKhauToiThieuValidator"},  # bản tiếng Việt của MinimumLengthValidator
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# Bootstrap: mặc định tải từ CDN (đúng đề cương) và tự chuyển sang bản trong static/vendor/bootstrap khi CDN lỗi.
# Đặt BOOTSTRAP_CUC_BO=1 trong .env để dùng ngay bản cục bộ (demo không có mạng, tránh chờ CDN hết thời gian).
BOOTSTRAP_CUC_BO = os.getenv("BOOTSTRAP_CUC_BO", "0") == "1"

# Mặc định email hiển thị trong console để kiểm thử phát triển; cấu hình SMTP qua biến môi trường khi triển khai.
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "1") == "1"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "0") == "1"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Tư vấn nông nghiệp <webmaster@localhost>")

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", str(BASE_DIR / "media")))

MESSAGE_TAGS = {message_constants.ERROR: "danger"}  # khớp class alert-danger của Bootstrap

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Khi chạy test dùng bộ băm mật khẩu nhanh để test không bị chậm (không ảnh hưởng khi chạy thật)
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
