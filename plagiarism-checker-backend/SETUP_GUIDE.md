🛠️ HƯỚNG DẪN SETUP & KHẮC PHỤC LỖI KHI CHUYỂN THƯ MỤC DỰ ÁN
📌 Lưu ý cốt lõi: Môi trường ảo của Python (.venv) ghi nhớ đường dẫn tuyệt đối của thư mục chứa nó. Do đó, khi bạn di chuyển dự án sang thư mục khác hoặc copy sang máy tính khác, cái .venv cũ sẽ bị "mù đường" và hỏng hoàn toàn.

Tuyệt đối KHÔNG mang theo thư mục .venv cũ. Hãy làm theo 5 bước "Đập đi xây lại" dưới đây:

Bước 1: Dọn dẹp tàn dư
Nếu trong thư mục dự án đang có sẵn thư mục .venv (do copy từ nơi khác mang tới), hãy Xóa (Delete) nó ngay lập tức.

Bước 2: Tạo môi trường ảo mới (Yêu cầu sự kiên nhẫn)
Mở Terminal tại thư mục gốc của Backend (ví dụ: plagiarism-checker-backend), gõ lệnh sau:

Bash
python -m venv .venv
⚠️ CẢNH BÁO QUAN TRỌNG: Phải chờ đến khi Terminal chạy xong hoàn toàn và hiện lại dấu nhắc lệnh (PS ...>). Tuyệt đối không ấn Ctrl + C hay tắt ngang cửa sổ lúc này, nếu không sẽ bị lỗi KeyboardInterrupt dẫn đến môi trường ảo bị rỗng, thiếu file Activate.ps1.

Mẹo nhỏ: Nếu VS Code báo lỗi đỏ "Unable to handle..." ở góc màn hình, đó chỉ là lỗi hiển thị (cache). Hãy ấn Ctrl + Shift + P, gõ Reload Window để VS Code làm mới lại.

Bước 3: Kích hoạt môi trường ảo
Gõ lệnh sau để đánh thức .venv:

Bash
.\.venv\Scripts\Activate.ps1
(Thành công khi bạn nhìn thấy chữ (.venv) màu xanh lá cây xuất hiện ở đầu dòng lệnh).

Bước 4: Cài đặt toàn bộ thư viện (Tránh lỗi ModuleNotFoundError)
Để tránh tình trạng chạy lên thiếu thư viện này, cài xong lại báo thiếu thư viện khác (như PyPDF2, passlib, jose...), hãy nạp toàn bộ danh sách phụ thuộc bằng 1 trong 2 cách:

Cách 1 (Chuẩn nhất - Khuyên dùng): Sử dụng file danh sách đã lưu sẵn:

Bash
pip install -r requirements.txt
Cách 2 (Cứu cánh - Nếu mất file requirements): Chạy lệnh tổng hợp này để cài "tất tay" các thư viện cốt lõi của hệ thống:

Bash
pip install PyPDF2 python-docx fastapi uvicorn sqlalchemy psycopg2-binary qdrant-client sentence-transformers underthesea python-multipart "passlib[bcrypt]" "python-jose[cryptography]"
Bước 5: Chốt hạ & Khởi động
Sau khi đảm bảo bước 4 đã chạy xong 100%, hãy gõ lệnh khởi động máy chủ FastAPI:

Bash
uvicorn main:app --reload
Hệ thống sẽ báo Application startup complete và chạy ổn định tại http://127.0.0.1:8000.