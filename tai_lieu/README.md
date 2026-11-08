# Tài liệu hỗ trợ đồ án

Thư mục này gom tư liệu **chính xác theo mã nguồn** để viết báo cáo, vẽ/đối chiếu sơ đồ UML và chuẩn bị demo.
Phân biệt hai loại file:

- **Sinh tự động từ mã nguồn** (không thể lệch hệ thống; có test canh, đổi code mà chưa chạy lại lệnh sinh thì test đỏ).
- **Viết tay** (cần cập nhật khi hệ thống đổi; riêng kịch bản demo có test chạy đúng trình tự).

| File | Loại | Nội dung |
|---|---|---|
| `TU_DIEN_DU_LIEU.md` | Sinh tự động | 14 bảng: cột, kiểu PostgreSQL, ràng buộc, khóa ngoại + sơ đồ ERD (Mermaid) |
| `MA_TRAN_PHAN_QUYEN.md` | Sinh tự động | 40 đường dẫn × 4 vai trò, phạm vi dữ liệu |
| `TEST_CASE_THU_CONG.md` / `.xlsx` | Sinh tự động (từ `kiem_thu_thu_cong/danh_sach.py`) | 69 test case thủ công; bản Excel có ô chọn «Đạt / Không đạt» |
| `RA_SOAT_UML.md` | Viết tay | Các chỗ hệ thống khác Phần A, đề xuất sửa sơ đồ hay sửa code; danh sách đối chiếu theo từng loại sơ đồ |
| `KICH_BAN_DEMO_10_PHUT.md` | Viết tay (có test) | Kịch bản 10 phút, phương án dự phòng, câu hỏi hội đồng |

## Cập nhật khi code thay đổi

```bash
python tai_lieu/tao_tai_lieu.py          # tạo lại từ điển dữ liệu và ma trận phân quyền
python kiem_thu_thu_cong/xuat.py          # tạo lại bảng test case (.md và .xlsx)
python manage.py test kiem_thu_thu_cong   # kiểm tra tài liệu, bảng test case và kịch bản demo còn đúng
```

## Tư liệu cho từng phần của báo cáo

Theo cấu trúc báo cáo bạn đã nêu. Báo cáo viết **từng chương một khi bạn yêu cầu**, lấy từ các file này.

| Phần báo cáo | Lấy tư liệu từ |
|---|---|
| Khảo sát và phân tích: use case, đặc tả use case | `MA_TRAN_PHAN_QUYEN.md`, `RA_SOAT_UML.md` mục B1, bảng test case (mỗi dòng là một kịch bản cụ thể) |
| Thiết kế: sơ đồ lớp, ERD, từ điển dữ liệu | `TU_DIEN_DU_LIEU.md` (ERD có sẵn), `RA_SOAT_UML.md` mục B2 |
| Thiết kế: tuần tự, hoạt động | `RA_SOAT_UML.md` mục B3, B4 |
| Thiết kế: kiến trúc MTV, phân quyền | `MA_TRAN_PHAN_QUYEN.md`; 9 app, mỗi app có `models.py`, `views.py`, `services.py` (nghiệp vụ), `templates/` |
| Cài đặt: quyết định kỹ thuật | `RA_SOAT_UML.md` mục A3 (công thức điểm, ngoài phạm vi, transaction, mã tự sinh, truy xuất) |
| Kiểm thử | `TEST_CASE_THU_CONG.md` (kết quả thực tế bạn điền), `python manage.py test` |
| Demo | `KICH_BAN_DEMO_10_PHUT.md` |

## Số liệu hệ thống (tại thời điểm tạo tài liệu, đã kiểm tra)

- 9 app Django (`taikhoan`, `danhmuc`, `tuvan`, `timkiem`, `hoidap`, `cauhinh`, `thongke`, `truyxuat`, `baocao`); 14 bảng; 40 đường dẫn; 33 template; 4 vai trò; 22 loại hành động ghi nhật ký.
- Khoảng 3365 dòng mã (không tính kiểm thử, migration) và 4287 dòng mã kiểm thử.
- Công nghệ (theo `requirements.txt`): Django 5.0 đến dưới 5.3, psycopg 3 (PostgreSQL), openpyxl, python-dotenv; giao diện Bootstrap 5.3.3. Lần chạy kiểm thử gần nhất dùng Django 5.2, Python 3.12, PostgreSQL 16.
- Quyết định kỹ thuật chính: tư vấn Rule-based (luật lưu CSDL, `condition_json` JSONB); lưu lịch sử tư vấn dạng bản chụp JSON (`ket_qua_json`); thao tác ghi nhiều bảng nằm trong `transaction.atomic`; khóa dòng (`select_for_update`) cho trọng số và câu trả lời; khóa tư vấn PostgreSQL cho mã tự sinh; `PROTECT` chặn xóa danh mục đang được dùng; chống chèn công thức khi xuất Excel.
