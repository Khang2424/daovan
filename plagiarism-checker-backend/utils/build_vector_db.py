import os
import sys
import PyPDF2
import uuid

# Đảm bảo script có thể nhận diện được các thư mục gốc của dự án
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import SourceDocument, Base
from services import model, qdrant_client, chunk_text_sliding_window
from qdrant_client.models import PointStruct
from underthesea import word_tokenize

# Thư mục chứa 24 file đồ án của bạn
DATA_DIR = "./data/source_docs"

def extract_text_local_pdf(file_path):
    """Hàm chuyên dụng để đọc file PDF từ ổ cứng (không dùng UploadFile)"""
    text = ""
    try:
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f" Lỗi khi đọc file {file_path}: {e}")
    return text.strip()

def main():
    print("=== BẮT ĐẦU CHƯƠNG TRÌNH XÂY DỰNG VECTOR DATABASE ===")
    
    # Kết nối Database
    db = SessionLocal()
    
    if not os.path.exists(DATA_DIR):
        print(f"Không tìm thấy thư mục {DATA_DIR}. Vui lòng tạo và bỏ PDF vào.")
        return

    # Lọc ra danh sách các file PDF
    files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    
    if not files:
        print("Thư mục trống. Hãy thả 24 file PDF của thầy hướng dẫn vào đây!")
        return

    print(f"Đã quét thấy {len(files)} file đồ án. Bắt đầu xử lý...\n")

    for file_name in files:
        file_path = os.path.join(DATA_DIR, file_name)
        print(f"[*] Đang xử lý: {file_name}")

        # 1. LƯU THÔNG TIN VÀO POSTGRESQL TRƯỚC ĐỂ LẤY ID CHUẨN
        # (Để tránh trùng lặp, ta có thể kiểm tra xem file này đã có trong DB chưa)
        existing_doc = db.query(SourceDocument).filter(SourceDocument.title == file_name).first()
        if existing_doc:
            print(f" -> File này đã có trong Database (ID: {existing_doc.id}). Bỏ qua.\n")
            continue

        new_doc = SourceDocument(
            title=file_name,
            author="Khoa CNTT - ĐH Lac Hong", # Bạn có thể sửa cứng tên trường vào đây
            file_path=file_path,
            sync_status="INDEXED"
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        doc_id = new_doc.id # Lấy được ID (ví dụ: 2, 3, 4...)

        # 2. ĐỌC CHỮ VÀ CẮT KHÚC (SLIDING WINDOW)
        text = extract_text_local_pdf(file_path)
        if not text:
            print(" -> File trống hoặc là file ảnh scan (AI không đọc được chữ). Bỏ qua.\n")
            continue
            
        chunks = chunk_text_sliding_window(text, window_size=3, overlap=1)
        
        # 3. BIẾN THÀNH VECTOR VÀ ĐẨY VÀO QDRANT
        points = []
        for i, chunk in enumerate(chunks):
            # Tách từ tiếng Việt chuẩn NLP
            chunk_segmented = word_tokenize(chunk, format="text")
            vector = model.encode(chunk_segmented)
            
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vector.tolist(),
                payload={
                    "source_doc_id": doc_id, # Đánh dấu đoạn văn này thuộc về file đồ án nào
                    "chunk_index": i,
                    "text": chunk
                }
            ))
        
        # Lưu vào Vector DB (Qdrant)
        if points:
            qdrant_client.upsert(
                collection_name="document_chunks",
                points=points
            )
        
        print(f" -> Thành công! Đã tạo {len(points)} Vectors vào Qdrant (Source ID: {doc_id})\n")

    print("\n=== HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ===")
    db.close()

if __name__ == "__main__":
    main()