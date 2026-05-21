import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "document_chunks"

# Thay tên file bạn muốn kiểm tra vào đây
FILE_NAME = "11190911_NguyenDinhChung_Thietkexaydungphanmemquanlysinhvien.pdf"

def verify_file_content(file_name):
    print(f"--- Đang kiểm tra dữ liệu của file: {file_name} ---")
    
    # 1. Kết nối Postgres để lấy ID (Số nguyên)
    try:
        db_conn = psycopg2.connect(
            host="localhost",
            database="daovan_logic_db", # Thay DB của bạn
            user="postgres",      # Thay username
            password="12345"   # Thay mật khẩu
        )
        cursor = db_conn.cursor()
        cursor.execute("SELECT id FROM source_documents WHERE file_path = %s", (file_name,))
        row = cursor.fetchone()
        
        if not row:
            print("❌ File này chưa được lưu trong Database PostgreSQL!")
            return
        
        doc_id_int = row[0]
        print(f"✅ Đã tìm thấy file trong Postgres với ID = {doc_id_int}")
        
    except Exception as e:
        print(f"❌ Lỗi kết nối Database: {e}")
        return
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'db_conn' in locals(): db_conn.close()

    # 2. Dùng ID số nguyên để truy vấn Qdrant
    results, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                # Đã sửa MatchValue từ file_name (String) thành doc_id_int (Integer)
                FieldCondition(key="source_doc_id", match=MatchValue(value=doc_id_int))
            ]
        ),
        limit=20, # Lấy thử 20 câu đầu tiên tìm thấy
        with_payload=True
    )

    if not results:
        print(f"❌ Không tìm thấy dữ liệu của ID {doc_id_int} trong Qdrant!")
        return

    print(f"\n✅ Đã tìm thấy dữ liệu trong Qdrant! Trích xuất 20 câu đầu tiên:\n")
    for i, point in enumerate(results):
        text = point.payload.get("text")
        print(f"Câu {i+1}: {text}")

if __name__ == "__main__":
    verify_file_content(FILE_NAME)