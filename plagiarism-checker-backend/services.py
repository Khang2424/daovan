import io
import PyPDF2
import docx
import re
import json
import os
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from underthesea import sent_tokenize

# [MỚI] Import thư viện SDK thế hệ mới của Google
from google import genai
from google.genai import types

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
    Kiểm tra đoạn văn có chứa dấu hiệu trích dẫn hay không bằng Regex.
    """
    quote_pattern = r'["“](.*?)["”]'
    has_quote_marks = bool(re.search(quote_pattern, text, flags=re.DOTALL))
    if has_quote_marks:
        return True
        
    ieee_pattern = r'\[\d+[^\]]*\]'
    apa_pattern = r'\([^)]*\d{4}[^)]*\)'
    
    tail_text = text[-80:]
    if bool(re.search(ieee_pattern, tail_text)) or bool(re.search(apa_pattern, tail_text)):
        return True
        
    return False

def split_main_and_references(text: str):
    """
    Tìm kiếm tiêu đề "Tài liệu tham khảo" và cắt văn bản thành 2 phần.
    """
    pattern = r'(?i)\n\s*(?:[IVX\d]+\.?\s*)?(?:DANH MỤC\s+)?TÀI LIỆU THAM KHẢO|REFERENCES|BIBLIOGRAPHY\s*\n'
    match = re.search(pattern, text)
    if match:
        ref_start = match.start()
        return text[:ref_start], text[ref_start:] 
    
    return text, ""

# ====================================================================
# 1. KHỞI TẠO CẤU HÌNH GEMINI (SDK MỚI)
# ====================================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("CẢNH BÁO: Chưa tìm thấy GEMINI_API_KEY trong file .env")

# Khởi tạo Client bằng thư viện mới
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ====================================================================
# 2. HÀM GIÁM KHẢO AI
# ====================================================================
def evaluate_plagiarism_with_gemini(student_text: str, source_text: str) -> dict:
    if not client:
         raise Exception("Server chưa được cấu hình API Key của Google.")

    prompt = f"""
    Bạn là một chuyên gia kiểm định đạo văn học thuật nghiêm khắc.
    Nhiệm vụ của bạn là so sánh ĐOẠN VĂN CỦA SINH VIÊN với NGUỒN DỮ LIỆU GỐC.
    
    ĐOẠN VĂN CỦA SINH VIÊN:
    "{student_text}"
    
    NGUỒN DỮ LIỆU GỐC:
    "{source_text}"
    
    Quy tắc phân loại:
    - EXACT_MATCH: Sao chép y nguyên hoặc chỉ thay đổi rất ít từ ngữ (giống >= 85%).
    - PARAPHRASED: Xào nấu từ ngữ (đạo ý), nhưng nội dung cốt lõi vẫn lấy từ nguồn gốc (giống từ 50% - 84%).
    - SAFE: Hai đoạn văn không liên quan nội dung (giống < 50%).
    """
    
    try:
        # Gọi SDK mới với tính năng ép schema
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', # Hoặc gemini-2.0-flash
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                # Ép AI phải trả về chuẩn JSON này, không được luyên thuyên
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "similarity_score": {"type": "NUMBER"},
                        "match_type": {"type": "STRING", "enum": ["EXACT_MATCH", "PARAPHRASED", "SAFE"]}
                    },
                    "required": ["similarity_score", "match_type"]
                },
            ),
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        print("\n" + "="*40)
        print("❌ LỖI GỌI GEMINI API:")
        print(f"Chi tiết: {str(e)}")
        print("="*40 + "\n")
        raise e 

# ====================================================================
# 3. [MỚI] HÀM THỢ HÀN - GỘP ĐOẠN VĂN (CHO FILE SCAN_ROUTER.PY GỌI)
# ====================================================================
def merge_overlapping_text(text1: str, text2: str) -> str:
    """
    Gộp 2 đoạn văn có phần trùng lặp ở giữa (do sliding window).
    Ví dụ: "A B C" và "C D E" -> "A B C D E"
    """
    # Tìm độ dài tối đa có thể trùng lặp
    max_overlap = min(len(text1), len(text2))
    
    # Lùi dần để tìm phần đuôi của text1 khớp với phần đầu của text2
    for i in range(max_overlap, 0, -1):
        if text1.endswith(text2[:i]):
            return text1 + text2[i:] # Hàn lại ngay tại điểm trùng khớp
            
    # Nếu không tìm thấy điểm chung, nối cách nhau 1 khoảng trắng
    return text1 + " " + text2