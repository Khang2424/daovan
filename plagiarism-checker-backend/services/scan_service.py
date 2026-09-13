import io
import re
import time
import fitz  # PyMuPDF
import docx
from fastapi import HTTPException, UploadFile
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from underthesea import sent_tokenize, word_tokenize
from sqlalchemy.orm import Session # [MỚI] Thêm type hint cho db session
from models import SourceDocument   # [MỚI] Gọi bảng SourceDocument để truy vấn tên đồ án nguồn

from services.ai_service import evaluate_plagiarism_with_gemini

print("Đang khởi động Model AI và Qdrant...")
MODEL_NAME = 'bkai-foundation-models/vietnamese-bi-encoder'
model = SentenceTransformer(MODEL_NAME)
qdrant_client = QdrantClient(host="localhost", port=6333)

async def extract_text_from_file(file: UploadFile):
    content = await file.read()
    text = ""
    
    if file.filename.endswith(".pdf"):
        # [SỬA LẠI] Dùng PyMuPDF (fitz) để bóc tách PDF, vá lỗi nứt chữ tiếng Việt
        doc = fitz.open(stream=content, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
            
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
# [MỚI] HÀM TIỀN XỬ LÝ "MẶT NẠ" (LOSSLESS PREPROCESSING) & TỪ VỰNG
# ====================================================================

def mask_abbreviations(text: str) -> str:
    """Tạm thời giấu dấu chấm (.) thành chuỗi _DOT_ để AI không cắt sai câu, bảo toàn 100% khoảng trắng gốc"""
    # 1. ASP. Net (Giữ nguyên khoảng trắng trước và sau dấu chấm bằng \2 và \3)
    text = re.sub(r'\b(ASP)(\s*)\.(\s*)(Net)\b', r'\1\2_DOT_\3\4', text, flags=re.IGNORECASE)
    
    # 2. Các chức danh tiếng Việt (PGS. TS.)
    text = re.sub(r'\b(ts|pgs|ths|vd|gs|bs)(\s*)\.', r'\1\2_DOT_', text, flags=re.IGNORECASE)
    
    # 3. Chức danh Thạc sĩ (Th.S.) - Cần bọc 2 dấu chấm
    text = re.sub(r'\b(th)(\s*)\.(\s*)(s)(\s*)\.', r'\1\2_DOT_\3\4\5_DOT_', text, flags=re.IGNORECASE)
    
    # 4. Từ viết tắt in hoa (N. X. B.)
    text = re.sub(r'\b([A-Z])(\s*)\.', r'\1\2_DOT_', text)
    
    return text

def unmask_abbreviations(text: str) -> str:
    """Gỡ mặt nạ, trả lại dấu chấm nguyên thủy cho văn bản"""
    return text.replace('_DOT_', '.')

def calculate_lexical_overlap(sentence: str, source_text: str) -> float:
    """Đo tỷ lệ từ vựng trùng khớp để loại bỏ lỗi 'vạ lây' do dùng context"""
    s_clean = re.sub(r'[^\w\s]', '', sentence.lower())
    db_clean = re.sub(r'[^\w\s]', '', source_text.lower())
    s_tokens = set(s_clean.split())
    db_tokens = set(db_clean.split())
    if not s_tokens: return 0.0
    return len(s_tokens.intersection(db_tokens)) / len(s_tokens)

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

# [MỚI] Bổ sung tham số db: Session vào process_text_plagiarism
def process_text_plagiarism(text: str, db: Session = None) -> list:
    query_vector = model.encode(word_tokenize(text, format="text"))
    search_response = qdrant_client.query_points(collection_name="document_chunks", query=query_vector.tolist(), limit=3)
    results = []
    
    # [MỚI] Lấy danh sách doc_ids để tra cứu tên tài liệu nguồn
    doc_ids = list({p.payload.get("source_doc_id") for p in search_response.points if p.payload.get("source_doc_id") is not None})
    doc_map = {}
    if db and doc_ids:
        docs = db.query(SourceDocument).filter(SourceDocument.id.in_(doc_ids)).all()
        doc_map = {d.id: {"title": d.title, "file_path": d.file_path} for d in docs}

    for point in search_response.points:
        match_type = "EXACT_MATCH" if point.score >= 0.85 else "PARAPHRASED" if point.score >= 0.50 else "SAFE"
        doc_id = point.payload.get("source_doc_id")
        doc_info = doc_map.get(doc_id, {})

        results.append({
            "source_doc_id": doc_id, 
            "source_title": doc_info.get("title") or f"Tài liệu #{doc_id}", # [MỚI] Bổ sung title
            "source_file_path": doc_info.get("file_path"),                  # [MỚI] Bổ sung file_path
            "matched_text": point.payload.get("text"),
            "similarity_score": round(point.score, 4), 
            "match_type": match_type
        })
    return results

# ====================================================================
# HÀM XỬ LÝ CHÍNH (THE CENTER-SENTENCE ARCHITECTURE)
# ====================================================================
# [MỚI] Bổ sung tham số db: Session để query tên đồ án nguồn từ Postgres
async def process_document_plagiarism(file: UploadFile, scan_mode: str, db: Session = None):
    document_text = await extract_text_from_file(file)
    if not document_text: raise ValueError("File trống")

    # 1. Tách văn bản thành TỪNG CÂU ĐƠN LẺ
    main_text, ref_text = split_main_and_references(document_text)
    
    # [SỬA LẠI] Đeo mặt nạ để bảo vệ dấu chấm
    main_text = mask_abbreviations(main_text)
    if ref_text: 
        ref_text = mask_abbreviations(ref_text)
    
    # AI cắt câu dựa trên văn bản đã mang mặt nạ (đảm bảo không đứt đoạn)
    main_sentences_masked = [s.strip() for s in sent_tokenize(main_text) if s.strip()]
    ref_sentences_masked = [s.strip() for s in sent_tokenize(ref_text) if s.strip()]
    
    # [SỬA LẠI] LẬP TỨC gỡ mặt nạ để trả lại văn bản gốc 100%
    main_sentences = [unmask_abbreviations(s) for s in main_sentences_masked]
    ref_sentences = [unmask_abbreviations(s) for s in ref_sentences_masked]
    
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
                
                # [SỬA LẠI] RAG Giai đoạn 2: Tính tỷ lệ trùng từ vựng để bác bỏ 'vạ lây'
                overlap_ratio = calculate_lexical_overlap(current_sentence, source_text_from_db)
                
                final_score = round(best_score, 4)
                final_match_type = "SAFE"

                if scan_mode == "offline":
                    # [SỬA LẠI] Đánh giá theo overlap_ratio
                    if overlap_ratio >= 0.75:
                        final_match_type = "EXACT_MATCH"
                    elif overlap_ratio >= 0.30:
                        final_match_type = "PARAPHRASED"
                    else:
                        final_match_type = "SAFE" # Từ chối kết quả vạ lây
                elif scan_mode == "hybrid":
                    if overlap_ratio >= 0.80:
                        final_match_type = "EXACT_MATCH"
                    else:
                        # [SỬA LẠI] Truyền current_sentence cho Gemini thay vì context_text
                        res = evaluate_plagiarism_with_gemini(current_sentence, source_text_from_db)
                        time.sleep(4)
                        final_match_type = res.get("match_type", "SAFE")
                elif scan_mode == "online":
                    # [SỬA LẠI] Truyền current_sentence cho Gemini thay vì context_text
                    res = evaluate_plagiarism_with_gemini(current_sentence, source_text_from_db)
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

    # ====================================================================
    # [MỚI] TRA CỨU TÊN ĐỒ ÁN NGUỒN TỪ POSTGRESQL (GẮN TITLE & FILE_PATH)
    # Gom toàn bộ source_doc_id lại và query 1 lượt để tối ưu hiệu năng
    # ====================================================================
    if db and all_matches:
        all_doc_ids = set()
        for item in all_matches:
            for s in item.get("sources", []):
                if s.get("source_doc_id") is not None:
                    all_doc_ids.add(s["source_doc_id"])
        
        if all_doc_ids:
            docs = db.query(SourceDocument).filter(SourceDocument.id.in_(list(all_doc_ids))).all()
            doc_map = {d.id: {"title": d.title, "file_path": d.file_path} for d in docs}
            
            # Gắn source_title và source_file_path vào từng nguồn
            for item in all_matches:
                for s in item.get("sources", []):
                    doc_id = s.get("source_doc_id")
                    info = doc_map.get(doc_id, {})
                    s["source_title"] = info.get("title") or f"Tài liệu #{doc_id}"
                    s["source_file_path"] = info.get("file_path") or ""

    # Không cần bộ lọc difflib hay thuật toán dọn rác nào nữa!
    return len(all_sentences), all_matches