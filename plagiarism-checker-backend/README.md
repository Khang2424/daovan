KIẾN TRÚC DỰ ÁN: HỆ THỐNG KIỂM TRA ĐẠO VĂN (BACKEND)
Dự án này được xây dựng dựa trên kiến trúc Clean Architecture của FastAPI, giúp phân tách rõ ràng các tầng logic, dễ dàng bảo trì và mở rộng. Dưới đây là giải thích chi tiết chức năng của từng thư mục và tệp tin trong hệ thống:

1. Các thư mục chính (Directories)
📁 routers/ (Tầng Giao tiếp API)
Thư mục này chứa các "cửa ngõ" (Endpoints) tiếp nhận yêu cầu từ người dùng (Frontend) và trả về kết quả.

auth_router.py: Xử lý toàn bộ các API liên quan đến tài khoản người dùng (Đăng ký, Đăng nhập để cấp JWT Token).

scan_router.py: Xử lý các API cốt lõi của hệ thống, bao gồm tiếp nhận văn bản, upload file tài liệu (.pdf, .docx), gọi AI để quét đạo văn và trả về báo cáo phân tích.

📁 utils/ (Kịch bản Tiện ích - Utility Scripts)
Thư mục chứa các tệp lệnh chạy độc lập, không gắn liền với quá trình chạy Server khởi động API. Dùng để thiết lập môi trường hoặc kiểm thử.

init_qdrant.py: Khởi tạo cấu trúc (Collection) ban đầu cho cơ sở dữ liệu Vector Qdrant.

reset_db.py: Kịch bản dọn dẹp, xóa trắng toàn bộ dữ liệu Vector cũ để test lại hệ thống từ đầu.

test_embedding.py & search_plagiarism.py: Các file viết kịch bản thử nghiệm lõi AI độc lập (chưa cần web) để chứng minh tính khả thi của thuật toán.

📁 Thư mục hệ thống (Tự động sinh ra)
.venv/: Môi trường ảo (Virtual Environment) chứa các thư viện Python dự án đang sử dụng. Không bao giờ đẩy thư mục này lên Github.

__pycache__/: Bộ nhớ đệm của Python giúp code chạy nhanh hơn.

2. Các tệp tin cốt lõi (Root Files)
Tầng Cấu hình & Khởi chạy (Core & Config)
main.py: Trái tim của toàn bộ hệ thống. File này khởi tạo Server FastAPI, gắn kết (include) các routers lại với nhau và cấu hình tài liệu Swagger UI. Khi chạy dự án, ta sẽ khởi động tệp tin này.

docker-compose.yml: Tệp tin cấu hình tự động tải và khởi chạy các cơ sở dữ liệu nền tảng (PostgreSQL, Qdrant) thông qua Docker.

Tầng Dữ liệu & Xác thực (Data & Security)
database.py: Nắm giữ "chìa khóa" kết nối hệ thống với hệ quản trị cơ sở dữ liệu PostgreSQL.

models.py: (Data Models) Ánh xạ các bảng trong CSDL PostgreSQL thành các Đối tượng Python (SQLAlchemy ORM). Quy định cấu trúc lưu trữ của User, Báo cáo (ScanReport), và Chi tiết trùng lặp (MatchDetail).

schemas.py: (Pydantic Schemas) Quy định hình dáng dữ liệu "gửi lên" và "trả về" ở các API. Giúp FastAPI tự động kiểm tra tính hợp lệ của dữ liệu đầu vào (Ví dụ: ép buộc người dùng phải gửi lên email và mật khẩu khi đăng ký).

auth.py: Trung tâm an ninh của hệ thống. Chứa các hàm băm mật khẩu, tạo thẻ thông hành (JWT Token), và hàm "lính gác" để chặn các truy cập trái phép.

Tầng Xử lý Logic (Business Logic)
services.py: Nơi chứa các thuật toán xử lý nặng nhất của hệ thống để các hàm trong routers gọi đến. Bao gồm:

Khởi tạo và nạp mô hình AI (Sentence Transformers).

Thuật toán trích xuất văn bản từ file PDF/Word.

Thuật toán chia nhỏ văn bản theo "Cửa sổ trượt" (Sliding Window) kết hợp NLP tách câu Tiếng Việt.