import io
import PyPDF2
import docx
import re
from fastapi import HTTPException, UploadFile
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from underthesea import sent_tokenize

print("Đang khởi động Model AI và Qdrant...")
MODEL_NAME = 'bkai-foundation-models/vietnamese-bi-encoder'
model = SentenceTransformer(MODEL_NAME)
qdrant_client = QdrantClient(host="localhost", port=6333)

async def extract_text_from_file(file: UploadFile):
    content = await file.read()
    text = ""
    if file.filename.endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    elif file.filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(content))
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ .pdf và .docx")
    return text.strip()

def chunk_text_sliding_window(text: str, window_size: int = 3, overlap: int = 1):
    sentences = sent_tokenize(text)
    chunks = []
    i = 0
    while i < len(sentences):
        chunk_sentences = sentences[i : i + window_size]
        chunk_text = " ".join(chunk_sentences)
        if chunk_text.strip():
            chunks.append(chunk_text)
        i += (window_size - overlap)
    return chunks
def check_if_quote(text: str) -> bool:
    """
    Hàm kiểm tra xem một đoạn văn (chunk) có phải là câu trích dẫn không.
    Sử dụng Regex để tìm các nội dung nằm giữa ngoặc kép thẳng ("") hoặc cong (“”).
    """
    # Tìm tất cả các chuỗi nằm trong ngoặc kép
    quotes = re.findall(r'["“](.*?)["”]', text)
    
    # Nếu không có ngoặc kép nào
    if not quotes:
        return False
        
    # Tính tổng số ký tự nằm trong ngoặc kép
    total_quote_length = sum(len(q) for q in quotes)
    
    # Do chunk có thể bị dính thêm cụm từ như 'Theo tác giả Nguyễn Văn A: "..."'
    # Nên nếu phần trong ngoặc kép chiếm hơn 40% độ dài đoạn, ta chốt nó là Trích dẫn!
    if total_quote_length / len(text) > 0.4:
        return True
        
    return False