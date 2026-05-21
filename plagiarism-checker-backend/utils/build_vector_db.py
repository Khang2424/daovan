import os
import uuid
import asyncio
import shutil
import traceback # [MỚI] Thư viện để in chi tiết lỗi
import psycopg2 # [MỚI] Thư viện kết nối Postgres
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from sentence_transformers import SentenceTransformer
from underthesea import sent_tokenize

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.scan_service import extract_text_from_file, mask_abbreviations, unmask_abbreviations, get_context_for_sentence

print("Đang tải Model AI cho Script Vector hóa...")
MODEL_NAME = 'bkai-foundation-models/vietnamese-bi-encoder'
model = SentenceTransformer(MODEL_NAME)
qdrant_client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "document_chunks"

class DummyUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content
    async def read(self):
        return self.content

async def process_and_vectorize_file(file_path: str, doc_id: str):
    print(f"\n▶ Đang xử lý file: {os.path.basename(file_path)}")
    
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    dummy_file = DummyUploadFile(file_path, file_content)
    document_text = await extract_text_from_file(dummy_file)
    
    if not document_text:
        print(f"Bỏ qua file rỗng: {file_path}")
        return True

    masked_text = mask_abbreviations(document_text)
    sentences_masked = [s.strip() for s in sent_tokenize(masked_text) if s.strip()]
    sentences = [unmask_abbreviations(s) for s in sentences_masked]
    
    points = []
    
    for index, current_sentence in enumerate(sentences):
        context_text = get_context_for_sentence(sentences, index)
        vector = model.encode(context_text).tolist()
        
        payload = {
            "source_doc_id": doc_id,
            "text": current_sentence, 
            "context_text": context_text
        }
        
        point_id = str(uuid.uuid4())
        points.append(PointStruct(id=point_id, vector=vector, payload=payload))
        
    if points:
        BATCH_SIZE = 100
        total_batches = (len(points) + BATCH_SIZE - 1) // BATCH_SIZE
        
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i : i + BATCH_SIZE]
            qdrant_client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"   -> Đã đẩy lô {i//BATCH_SIZE + 1}/{total_batches} ({len(batch)} câu)...")
            
        print(f" => HOÀN TẤT file! Tổng cộng {len(points)} câu.")
    return True

async def main():
    if not qdrant_client.collection_exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' chưa tồn tại. Đang tạo mới...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
    
    # [MỚI] THIẾT LẬP KẾT NỐI POSTGRESQL
    # Hãy thay đổi user, password, dbname cho khớp với máy của bạn
    db_conn = psycopg2.connect(
        host="localhost",
        database="daovan_logic_db", # Thay tên DB của bạn vào đây
        user="postgres",      # Thay username của bạn
        password="12345"   # Thay mật khẩu của bạn
    )
    cursor = db_conn.cursor()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.abspath(os.path.join(current_dir, "..", "data", "source_docs"))
    done_folder = os.path.abspath(os.path.join(current_dir, "..", "data", "done"))
    error_folder = os.path.abspath(os.path.join(current_dir, "..", "data", "error"))
    os.makedirs(done_folder, exist_ok=True)
    os.makedirs(error_folder, exist_ok=True)
    
    if not os.path.exists(data_folder):
        print(f"Không tìm thấy thư mục {data_folder}")
        return

    files = [f for f in os.listdir(data_folder) if f.endswith(('.pdf', '.docx'))]
    print(f"Tìm thấy {len(files)} file cần Vector hóa.")
    
    for filename in files:
        file_path = os.path.join(data_folder, filename)
        
        try:
            # ========================================================
            # [MỚI] LOGIC ĐỒNG BỘ INTEGER ID VỚI POSTGRESQL
            # 1. Kiểm tra xem file đã có trong bảng source_documents chưa
            cursor.execute("SELECT id FROM source_documents WHERE file_path = %s", (filename,))
            row = cursor.fetchone()
            
            if row:
                doc_id_int = row[0] # Nếu có rồi thì lấy ID cũ
            else:
                # 2. Nếu chưa có, thêm mới và lấy ID tự động tăng về
                cursor.execute(
                    "INSERT INTO source_documents (file_path, title) VALUES (%s, %s) RETURNING id", 
                    (filename, filename)
        )
                doc_id_int = cursor.fetchone()[0]
                db_conn.commit() # Lưu vào DB
            # ========================================================

            # GỌI HÀM VECTOR VỚI ID LÀ SỐ NGUYÊN
            success = await process_and_vectorize_file(file_path, doc_id=doc_id_int)
            
            if success:
                done_path = os.path.join(done_folder, filename)
                shutil.move(file_path, done_path)
                print(f" ✔ Đã chuyển {filename} sang thư mục done/")
                
        except Exception as e:
            print(f"\n ❌ LỖI NGHIÊM TRỌNG Ở FILE {filename}: {str(e)}")
            error_path = os.path.join(error_folder, filename)
            shutil.move(file_path, error_path)
            db_conn.rollback() # Trả lại trạng thái DB nếu có lỗi
            print(f" ⛑ Đã CÁCH LY file lỗi sang thư mục error/ để hệ thống chạy tiếp!")

    cursor.close()
    db_conn.close()
    print("\n🎉 HOÀN TẤT VECTOR HÓA TOÀN BỘ DỮ LIỆU!")
if __name__ == "__main__":
    asyncio.run(main())