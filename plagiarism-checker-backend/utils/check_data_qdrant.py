from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "document_chunks"

# Thay tên file bạn muốn kiểm tra vào đây
FILE_NAME = "11190911_NguyenDinhChung_Thietkexaydungphanmemquanlysinhvien.pdf"

def verify_file_content(file_name):
    print(f"--- Đang kiểm tra dữ liệu của file: {file_name} ---")
    
    # Dùng hàm scroll để lấy dữ liệu theo filter
    results, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="source_doc_id", match=MatchValue(value=file_name))
            ]
        ),
        limit=20, # Lấy thử 20 câu đầu tiên tìm thấy
        with_payload=True
    )

    if not results:
        print("❌ Không tìm thấy dữ liệu của file này trong Qdrant!")
        return

    for i, point in enumerate(results):
        text = point.payload.get("text")
        print(f"Câu {i+1}: {text}")

if __name__ == "__main__":
    verify_file_content(FILE_NAME)