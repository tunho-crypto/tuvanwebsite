# Ma trận phân quyền

Sinh tự động từ mã nguồn: **40 đường dẫn** (khai báo `vai_tro_cho_phep` của từng view). ✔ = được phép.

Các đường dẫn ghi «Công khai» dùng được khi chưa đăng nhập; những đường dẫn còn lại chuyển về `/dang-nhap/?next=...` (302). Đã đăng nhập nhưng sai vai trò → trang 403; tài khoản bị khóa → bị đăng xuất ở yêu cầu kế tiếp.

| Đường dẫn | Chức năng | Phương thức | Quản trị | Biên tập | Chuyên gia | Nông dân | Phạm vi dữ liệu |
|---|---|---|---|---|---|---|---|
| `/` | Trang chủ (công khai trước đăng nhập) | GET | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/bao-cao/` | Trang báo cáo | GET | ✔ |  |  |  |  |
| `/bao-cao/cay-trong/` | Tải Excel cây trồng | GET | ✔ |  |  |  |  |
| `/bao-cao/lich-su-tu-van/` | Tải Excel lịch sử tư vấn | GET | ✔ |  |  |  |  |
| `/bao-cao/luat-tu-van/` | Tải Excel luật hiện hành | GET | ✔ |  |  |  |  |
| `/bao-cao/thong-ke/` | Thống kê (có xuất Excel với ?xuat=xlsx) | GET | ✔ |  |  |  |  |
| `/cau-hinh/` | Cấu hình trọng số w1, w2, w3 | GET, POST | ✔ |  |  |  |  |
| `/dang-ky/` | Đăng ký tài khoản nông dân | GET, POST | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/dang-nhap/` | Đăng nhập | GET, POST | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/dang-xuat/` | Đăng xuất (chỉ POST) | POST | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/danh-muc/<muc>/` | Xem danh mục (5 bảng) | GET | ✔ | ✔ | ✔ | ✔ |  |
| `/danh-muc/<muc>/<id>/sua/` | Sửa bản ghi danh mục | GET, POST | ✔ | ✔ |  |  |  |
| `/danh-muc/<muc>/<id>/xoa/` | Xóa bản ghi danh mục | GET, POST | ✔ | ✔ |  |  |  |
| `/danh-muc/<muc>/them/` | Thêm bản ghi danh mục | GET, POST | ✔ | ✔ |  |  |  |
| `/doi-mat-khau/` | Đổi mật khẩu của chính mình | GET, POST | ✔ | ✔ | ✔ | ✔ |  |
| `/gioi-thieu/` | Giới thiệu hệ thống (menu thành viên) | GET | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/hoi-dap/` | Danh sách câu hỏi | GET | ✔ |  | ✔ | ✔ | Nông dân chỉ thấy câu hỏi của mình |
| `/hoi-dap/<id>/` | Xem câu hỏi và câu trả lời | GET | ✔ |  | ✔ | ✔ | Nông dân chỉ mở được câu hỏi của mình (của người khác: 404) |
| `/hoi-dap/<id>/tra-loi/` | Chuyên gia trả lời | GET, POST |  |  | ✔ |  | Chỉ khi câu hỏi đang «Chờ trả lời» |
| `/hoi-dap/them/` | Đặt câu hỏi | GET, POST |  |  |  | ✔ |  |
| `/nguoi-dung/` | Danh sách người dùng | GET | ✔ |  |  |  |  |
| `/nguoi-dung/<id>/khoa/` | Khóa / mở khóa tài khoản (POST) | POST | ✔ |  |  |  |  |
| `/nguoi-dung/<id>/sua/` | Sửa người dùng | GET, POST | ✔ |  |  |  |  |
| `/nguoi-dung/them/` | Thêm người dùng | GET, POST | ✔ |  |  |  |  |
| `/nhat-ky/` | Nhật ký hệ thống | GET | ✔ |  |  |  |  |
| `/quen-mat-khau/` | Yêu cầu mã khôi phục mật khẩu qua email | GET, POST | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/quen-mat-khau/da-gui/` | Thông báo đã gửi mã khôi phục | GET | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/quen-mat-khau/hoan-tat/` | Thông báo đặt lại mật khẩu thành công | GET | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/quen-mat-khau/nhap-ma/` | Xác minh mã email và đặt mật khẩu mới | GET, POST | ✔ | ✔ | ✔ | ✔ | Công khai |
| `/tim-kiem/` | Tìm kiếm cây trồng, kỹ thuật, mùa vụ | GET | ✔ | ✔ | ✔ | ✔ |  |
| `/truy-xuat/` | Truy xuất nguồn: luật → tài liệu | GET | ✔ | ✔ | ✔ | ✔ |  |
| `/tu-van/` | Form tư vấn, «Xem kết quả» (ghi lịch sử) | GET, POST | ✔ | ✔ | ✔ | ✔ |  |
| `/tu-van/api-tinh-diem/` | API tính nhanh, không ghi CSDL (POST) | POST | ✔ | ✔ | ✔ | ✔ | Không ghi CSDL |
| `/tu-van/lich-su/` | Danh sách lịch sử tư vấn | GET | ✔ | ✔ | ✔ | ✔ | Nông dân chỉ thấy lịch sử của mình |
| `/tu-van/lich-su/<id>/` | Kết quả đã lưu của một lần tư vấn | GET | ✔ | ✔ | ✔ | ✔ | Nông dân chỉ mở được của mình (của người khác: 404) |
| `/tu-van/luat/` | Danh sách luật tư vấn | GET | ✔ | ✔ |  |  |  |
| `/tu-van/luat/<id>/bat-tat/` | Bật / tắt luật (POST) | POST | ✔ | ✔ |  |  |  |
| `/tu-van/luat/<id>/sua/` | Sửa luật | GET, POST | ✔ | ✔ |  |  |  |
| `/tu-van/luat/<id>/xoa/` | Xóa luật | GET, POST | ✔ | ✔ |  |  |  |
| `/tu-van/luat/them/` | Thêm luật | GET, POST | ✔ | ✔ |  |  |  |
