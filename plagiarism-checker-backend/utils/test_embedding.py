from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

# 1. Khởi tạo model AI tiếng Việt
# LƯU Ý: Lần chạy đầu tiên sẽ mất một lúc để tải file model (khoảng ~500MB) về máy.
model_name = 'bkai-foundation-models/vietnamese-bi-encoder'
print(f"Đang tải model '{model_name}' (Vui lòng đợi)...")
model = SentenceTransformer(model_name)

# 2. Câu văn tiếng Việt cần thử nghiệm (Lấy từ file test của bạn)
text = "Trí tuệ nhân tạo hay trí thông minh nhân tạo là một ngành thuộc lĩnh vực khoa học máy tính."

# 3. Biến câu văn thành mảng Vector
vector = model.encode(text)
print(f"Đã tạo Vector thành công! Kích thước: {len(vector)} chiều.")

# 4. Đẩy Vector này vào Qdrant Database
client = QdrantClient(host="localhost", port=6333)

# Tạo một ID ngẫu nhiên cho point này
point_id = str(uuid.uuid4())

client.upsert(
    collection_name="document_chunks",
    points=[
        PointStruct(
            id=point_id,
            vector=vector.tolist(), # Bắt buộc phải chuyển từ Numpy Array sang List
            payload={
                "source_doc_id": 1, # ID giả lập của tài liệu nguồn
                "chunk_index": 0,
                "text": text        # Lưu lại văn bản gốc để dễ hiển thị sau này
            }
        )
    ]
)

print(f"Đã lưu thành công Vector vào Qdrant với ID: {point_id}")