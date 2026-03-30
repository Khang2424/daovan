from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# 1. Kết nối tới Qdrant đang chạy qua Docker
client = QdrantClient(host="localhost", port=6333)

collection_name = "document_chunks"

# 2. Kiểm tra xem Collection đã tồn tại chưa, nếu chưa thì tạo mới
if not client.collection_exists(collection_name=collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=768, # BẮT BUỘC LÀ 768: Đây là số chiều vector đầu ra của mô hình vietnamese-bi-encoder
            distance=Distance.COSINE # Sử dụng khoảng cách Cosine để so sánh độ tương đồng ngữ nghĩa
        ),
    )
    print(f"Đã tạo thành công Collection: '{collection_name}' với vector size 768.")
else:
    print(f"Collection '{collection_name}' đã tồn tại.")

# 3. Lấy thông tin Collection để xác nhận
collection_info = client.get_collection(collection_name=collection_name)
print(f"Trạng thái Collection: {collection_info.status}")