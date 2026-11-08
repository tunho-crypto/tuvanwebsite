"""Dữ liệu mẫu dùng cho lệnh nap_du_lieu_mau (và dùng lại ở test cho danh mục cố định)."""

VAI_TRO = [
    ("ADMIN", "Quản trị hệ thống", "Quản lý người dùng, nhật ký, danh mục, cấu hình trọng số, báo cáo"),
    ("BIEN_TAP", "Biên tập viên", "Quản lý danh mục và luật tư vấn"),
    ("CHUYEN_GIA", "Chuyên gia", "Trả lời câu hỏi, xem lịch sử tư vấn"),
    ("NONG_DAN", "Nông dân", "Tra cứu, tư vấn, đặt câu hỏi"),
]

# (username, họ, tên, mã vai trò)
TAI_KHOAN = [
    ("admin", "Nguyễn Quản", "Trị", "ADMIN"),
    ("bientap", "Trần Biên", "Tập", "BIEN_TAP"),
    ("chuyengia", "Lê Chuyên", "Gia", "CHUYEN_GIA"),
    ("nongdan", "Phạm Nông", "Dân", "NONG_DAN"),
]
MAT_KHAU_MAC_DINH = "123456"

# (ma_cay, ten_cay, nhom_cay, dac_diem) - 12 cây, 3 nhóm
CAY_TRONG = [
    ("CA_PHE", "Cà phê", "CONG_NGHIEP", "Cây công nghiệp chủ lực của Tây Nguyên, ưa khí hậu mát, đất bazan"),
    ("HO_TIEU", "Hồ tiêu", "CONG_NGHIEP", "Cây leo trụ, cần thoát nước tốt, giá trị xuất khẩu cao"),
    ("CAO_SU", "Cao su", "CONG_NGHIEP", "Cây thân gỗ, khai thác mủ sau 6-7 năm"),
    ("DIEU", "Điều", "CONG_NGHIEP", "Chịu hạn tốt, thích hợp đất xám"),
    ("SAU_RIENG", "Sầu riêng", "AN_QUA", "Cây ăn quả giá trị kinh tế cao, cần chống úng mùa mưa"),
    ("BO", "Bơ", "AN_QUA", "Cây ăn quả ưa mát, phát triển tốt ở vùng cao"),
    ("CHANH_DAY", "Chanh dây", "AN_QUA", "Cây dây leo, thu hoạch sau 6-8 tháng"),
    ("MIT", "Mít", "AN_QUA", "Dễ trồng, chịu hạn khá"),
    ("LUA", "Lúa nước", "NGAN_NGAY", "Cây lương thực, trồng vùng trũng chủ động nước"),
    ("NGO", "Ngô", "NGAN_NGAY", "Cây lương thực và thức ăn chăn nuôi, trồng đầu mùa mưa"),
    ("SAN", "Sắn", "NGAN_NGAY", "Chịu hạn, đất nghèo dinh dưỡng"),
    ("LAC", "Đậu phộng", "NGAN_NGAY", "Cây họ đậu, cải tạo đất"),
]

TINH_THANH = [
    ("KON_TUM", "Kon Tum"),
    ("GIA_LAI", "Gia Lai"),
    ("DAK_LAK", "Đăk Lăk"),
    ("DAK_NONG", "Đăk Nông"),
    ("LAM_DONG", "Lâm Đồng"),
]

# (ma_mua, ten_mua, từ tháng, đến tháng)
MUA_VU = [
    ("MUA_MUA", "Mùa mưa", 5, 10),
    ("MUA_KHO", "Mùa khô", 11, 4),
]

# (ma_tl, ten_tl, nguon_tham_chieu)
TAI_LIEU = [
    ("TL_WASI_01", "Quy trình kỹ thuật trồng trọt cây công nghiệp và cây ăn quả Tây Nguyên", "WASI"),
    ("TL_SONN_DL", "Hướng dẫn cơ cấu cây trồng theo mùa vụ tỉnh Đăk Lăk", "Sở Nông nghiệp và Môi trường Đăk Lăk"),
]

KY_THUAT = [
    ("KT_TUOI_CF", "Kỹ thuật tưới tiết kiệm nước cho cà phê", "Tưới nước", "Tưới gốc 3-4 đợt mùa khô, 450-600 lít/gốc/đợt"),
    ("KT_THOAT_SR", "Làm rãnh thoát nước cho sầu riêng mùa mưa", "Phòng bệnh", "Đắp mô, làm rãnh thoát nước để hạn chế úng và bệnh thối rễ"),
]

# Trọng số mặc định (w1 + w2 + w3 = 1)
CAU_HINH = [("w1", "0.5"), ("w2", "0.3"), ("w3", "0.2")]

# Luật tư vấn mẫu:
# (rule_id, ma_cay, ma_tinh|None, ma_mua|None, từ khóa nhu cầu, score_weight, ma_tl, is_active)
LUAT_TU_VAN = [
    ("LT20260101-001", "SAU_RIENG", "DAK_LAK", "MUA_MUA", ["gia tri cao", "kinh te cao"], "1.00", "TL_WASI_01", True),
    ("LT20260101-002", "CA_PHE", "DAK_LAK", "MUA_MUA",
     ["gia tri cao", "kinh te cao", "gia tri kinh te", "cay cong nghiep"], "1.00", "TL_SONN_DL", True),
    ("LT20260101-003", "HO_TIEU", None, None, ["gia tri cao", "kinh te cao"], "1.00", "TL_WASI_01", True),
    ("LT20260101-004", "BO", "LAM_DONG", "MUA_KHO", ["gia tri cao", "an qua"], "1.00", "TL_WASI_01", True),
    ("LT20260101-005", "NGO", "DAK_NONG", "MUA_MUA", ["cay ngan ngay", "luong thuc"], "1.00", "TL_WASI_01", True),
    ("LT20260101-006", "SAN", "GIA_LAI", "MUA_MUA", ["cay ngan ngay", "luong thuc"], "1.00", "TL_WASI_01", True),
    # Luật đang tắt: dùng để kiểm tra is_active
    ("LT20260101-007", "CHANH_DAY", "LAM_DONG", "MUA_KHO", ["gia tri cao"], "1.00", "TL_WASI_01", False),
]
