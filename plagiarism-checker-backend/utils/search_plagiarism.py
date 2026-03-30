from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from underthesea import word_tokenize # THÊM THƯ VIỆN NÀY
import uuid

# 1. Khởi tạo model AI
model_name = 'bkai-foundation-models/vietnamese-bi-encoder'
model = SentenceTransformer(model_name)
client = QdrantClient(host="localhost", port=6333)

print("--- BƯỚC 1: LƯU ĐỒ ÁN MẪU VÀO DB ---")
text_goc = "Trí tuệ nhân tạo hay trí thông minh nhân tạo là một ngành thuộc lĩnh vực khoa học máy tính."

# TÁCH TỪ TIẾNG VIỆT TRƯỚC KHI ĐƯA VÀO AI
text_goc_segmented = word_tokenize(text_goc, format="text")
print(f"Sau khi tách từ: {text_goc_segmented}") 

vector_goc = model.encode(text_goc_segmented)

client.upsert(
    collection_name="document_chunks",
    points=[PointStruct(id=str(uuid.uuid4()), vector=vector_goc.tolist(), payload={"source_doc_id": 1, "text": text_goc})]
)

print("\n--- BƯỚC 2: SINH VIÊN NỘP BÀI KIỂM TRA ---")
query_text = "AI là một chuyên ngành của khoa học máy tính tập trung vào việc tạo ra các máy móc thông minh."

# TÁCH TỪ CHO CÂU CỦA SINH VIÊN
query_segmented = word_tokenize(query_text, format="text")
query_vector = model.encode(query_segmented)

print("Đang quét đối chiếu...\n")
search_response = client.query_points(collection_name="document_chunks", query=query_vector.tolist(), limit=1)
search_results = search_response.points

if search_results:
    best_match = search_results[0]
    score = best_match.score
    
    print("=== KẾT QUẢ KIỂM TRA ĐẠO VĂN ===")
    print(f"Câu gốc: '{best_match.payload['text']}'")
    print(f"Câu nghi vấn: '{query_text}'")
    print(f"Độ tương đồng (Cosine Score): {score:.4f}")