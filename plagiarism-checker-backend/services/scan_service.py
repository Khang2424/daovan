import io
import re
import time
import PyPDF2
import docx
from fastapi import HTTPException, UploadFile
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from underthesea import sent_tokenize, word_tokenize

from services.ai_service import evaluate_plagiarism_with_gemini

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
            if page.extract_text(): text += page.extract_text() + "\n"
    elif file.filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(content))
        for para in doc.paragraphs:
            if para.text.strip(): text += para.text + "\n"
    else:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ .pdf và .docx")
    return text.strip()

def split_main_and_references(text: str):
    match = re.search(r'(?i)\n\s*(?:[IVX\d]+\.?\s*)?(?:DANH MỤC\s+)?TÀI LIỆU THAM KHẢO|REFERENCES|BIBLIOGRAPHY\s*\n', text)
    if match: return text[:match.start()], text[match.start():]
    return text, ""

def check_if_quote(text: str) -> bool:
    if bool(re.search(r'["“](.*?)["”]', text, flags=re.DOTALL)): return True
    tail_text = text[-80:]
    if bool(re.search(r'\[\d+[^\]]*\]', tail_text)) or bool(re.search(r'\([^)]*\d{4}[^)]*\)', tail_text)): return True
    return False

# ====================================================================
# [MỚI] HÀM SINH NGỮ CẢNH (CHỈ LẤY TEXT, KHÔNG GỘP DATA)
# ====================================================================
def get_context_for_sentence(sentences: list, index: int) -> str:
    """Tạo cửa sổ ngữ cảnh bao quanh câu trọng tâm i"""
    n = len(sentences)
    if n == 1:
        return sentences[0]
    if index == 0:
        return sentences[0] + " " + sentences[1]
    if index == n - 1:
        return sentences[n - 2] + " " + sentences[n - 1]
    
    return sentences[index - 1] + " " + sentences[index] + " " + sentences[index + 1]

def process_text_plagiarism(text: str) -> list:
    query_vector = model.encode(word_tokenize(text, format="text"))
    search_response = qdrant_client.query_points(collection_name="document_chunks", query=query_vector.tolist(), limit=3)
    results = []
    for point in search_response.points:
        match_type = "EXACT_MATCH" if point.score >= 0.85 else "PARAPHRASED" if point.score >= 0.50 else "SAFE"
        results.append({
            "source_doc_id": point.payload.get("source_doc_id"), "matched_text": point.payload.get("text"),
            "similarity_score": round(point.score, 4), "match_type": match_type
        })
    return results

# ====================================================================
# HÀM XỬ LÝ CHÍNH (THE CENTER-SENTENCE ARCHITECTURE)
# ====================================================================
async def process_document_plagiarism(file: UploadFile, scan_mode: str):
    document_text = await extract_text_from_file(file)
    if not document_text: raise ValueError("File trống")

    # 1. Tách văn bản thành TỪNG CÂU ĐƠN LẺ
    main_text, ref_text = split_main_and_references(document_text)
    
    # Sửa lỗi NLP hay cắt nhầm chữ "ASP. Net"
    main_text = main_text.replace("ASP. Net", "ASP.Net")
    ref_text = ref_text.replace("ASP. Net", "ASP.Net")
    
    main_sentences = [s.strip() for s in sent_tokenize(main_text) if s.strip()]
    ref_sentences = [s.strip() for s in sent_tokenize(ref_text) if s.strip()]
    
    all_sentences = main_sentences + ref_sentences
    ref_start_index = len(main_sentences)

    all_matches = []
    
    # 2. Vòng lặp quét TỪNG CÂU TRỌNG TÂM
    for index, current_sentence in enumerate(all_sentences):
        
        # Tạo cục Text có chứa ngữ cảnh để đưa cho AI đọc hiểu
        context_text = get_context_for_sentence(all_sentences, index)
        
        query_vector = model.encode(word_tokenize(context_text, format="text"))
        search_response = qdrant_client.query_points(collection_name="document_chunks", query=query_vector.tolist(), limit=1)

        if search_response.points:
            best_point = search_response.points[0]
            best_score = best_point.score
            
            if best_score >= 0.50:
                source_text_from_db = best_point.payload.get("text")
                final_score, final_match_type = round(best_score, 4), "SAFE"

                if scan_mode == "offline":
                    final_match_type = "EXACT_MATCH" if best_score >= 0.85 else "PARAPHRASED"
                elif scan_mode == "hybrid":
                    if best_score >= 0.85:
                        final_match_type = "EXACT_MATCH"
                    else:
                        res = evaluate_plagiarism_with_gemini(context_text, source_text_from_db)
                        time.sleep(4)
                        final_match_type = res.get("match_type", "SAFE")
                elif scan_mode == "online":
                    res = evaluate_plagiarism_with_gemini(context_text, source_text_from_db)
                    time.sleep(4)
                    final_score, final_match_type = res.get("similarity_score", final_score), res.get("match_type", "SAFE")

                if final_match_type != "SAFE":
                    # [CHỐT HẠ] Gắn kết quả vào ĐÚNG CÂU ĐÓ (current_sentence)
                    all_matches.append({
                        "chunk_index": index + 1, 
                        "student_text": current_sentence, # Text tinh khiết, 0% trùng lặp
                        "is_quote": check_if_quote(current_sentence), 
                        "is_reference": index >= ref_start_index,
                        "sources": [{
                            "source_doc_id": best_point.payload.get("source_doc_id"),
                            "matched_text": source_text_from_db,
                            "similarity_score": final_score,
                            "match_type": final_match_type
                        }]
                    })

    # Không cần bộ lọc difflib hay thuật toán dọn rác nào nữa!
    return len(all_sentences), all_matches