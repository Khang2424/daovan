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
    Kiểm tra đoạn văn có chứa dấu hiệu trích dẫn hay không bằng Regex.
    Bắt 2 trường hợp: Có dấu ngoặc kép HOẶC có định dạng dẫn nguồn ở cuối đoạn.
    """
    # ---------------------------------------------------------
    # TRƯỜNG HỢP 1: TÌM DẤU NGOẶC KÉP (Dành cho trích dẫn ngắn)
    # ---------------------------------------------------------
    # Hỗ trợ cả ngoặc kép tiếng Việt (“ ”) và tiếng Anh (" ")
    # cờ re.DOTALL giúp Regex đọc xuyên qua cả các dấu xuống dòng (\n)
    quote_pattern = r'["“](.*?)["”]'
    has_quote_marks = bool(re.search(quote_pattern, text, flags=re.DOTALL))
    
    if has_quote_marks:
        return True
        
    # ---------------------------------------------------------
    # TRƯỜNG HỢP 2: TÌM KÝ HIỆU DẪN NGUỒN (Dành cho trích dẫn khối dài)
    # ---------------------------------------------------------
    # Chuẩn IEEE: Tìm cụm ngoặc vuông chứa số. VD: [1], [15], [4, tr.97]
    ieee_pattern = r'\[\d+[^\]]*\]'
    
    # Chuẩn APA/Harvard: Tìm cụm ngoặc đơn có chứa 4 chữ số liên tiếp (năm xuất bản)
    # VD: (Tác giả, 2023), (Smith, 2020, tr.15)
    apa_pattern = r'\([^)]*\d{4}[^)]*\)'
    
    # Đối với trích dẫn khối (không có ngoặc kép), nguồn thường nằm ở cuối đoạn.
    # Ta cắt khoảng 80 ký tự cuối cùng của đoạn văn để rà soát.
    tail_text = text[-80:]
    if bool(re.search(ieee_pattern, tail_text)) or bool(re.search(apa_pattern, tail_text)):
        return True
        
    return False

def split_main_and_references(text: str):
    """
    Tìm kiếm tiêu đề "Tài liệu tham khảo" và cắt văn bản thành 2 phần: 
    Phần nội dung chính và Phần danh mục tham khảo.
    """
    # Regex tìm các chữ như: "TÀI LIỆU THAM KHẢO", "DANH MỤC TÀI LIỆU THAM KHẢO", "REFERENCES"
    # Hỗ trợ cả trường hợp có số la mã phía trước (VD: VI. TÀI LIỆU THAM KHẢO)
    pattern = r'(?i)\n\s*(?:[IVX\d]+\.?\s*)?(?:DANH MỤC\s+)?TÀI LIỆU THAM KHẢO|REFERENCES|BIBLIOGRAPHY\s*\n'
    
    match = re.search(pattern, text)
    if match:
        ref_start = match.start()
        return text[:ref_start], text[ref_start:] # Trả về (Nội dung chính, Phần tham khảo)
    
    return text, "" # Nếu không tìm thấy, coi như toàn bộ là nội dung chính