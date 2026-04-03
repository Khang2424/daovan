import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from underthesea import word_tokenize

from database import get_db
from models import User, ScanReport, MatchDetail
from schemas import ScanRequest
from auth import get_current_user
from services import model, qdrant_client, extract_text_from_file, chunk_text_sliding_window, check_if_quote, split_main_and_references

# Khởi tạo Router
router = APIRouter(prefix="/api/v1/scan", tags=["Scanner"])

@router.post("/text")
async def scan_plagiarism_text(request: ScanRequest, current_user: User = Depends(get_current_user)):
    try:
        query_segmented = word_tokenize(request.text, format="text")
        query_vector = model.encode(query_segmented)
        search_response = qdrant_client.query_points(
            collection_name="document_chunks", query=query_vector.tolist(), limit=3
        )
        results = []
        for point in search_response.points:
            score = point.score
            match_type = "EXACT_MATCH" if score >= 0.85 else "PARAPHRASED" if score >= 0.50 else "SAFE"
            results.append({
                "source_doc_id": point.payload.get("source_doc_id"),
                "matched_text": point.payload.get("text"),
                "similarity_score": round(score, 4),
                "match_type": match_type
            })
        return {"status": "success", "user_email": current_user.email, "query_text": request.text, "matches": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@router.post("/file")
async def scan_file_plagiarism(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    try:
        document_text = await extract_text_from_file(file)
        if not document_text:
            raise HTTPException(status_code=400, detail="File trống")

        # ========================================================
        # [MỚI] 1. CẮT ĐUÔI VĂN BẢN VÀ BĂM (CHUNKING) RIÊNG BIỆT
        # ========================================================
        main_text, ref_text = split_main_and_references(document_text)
        
        main_chunks = chunk_text_sliding_window(main_text, window_size=3, overlap=1)
        ref_chunks = chunk_text_sliding_window(ref_text, window_size=3, overlap=1) if ref_text else []
        
        # Gộp lại thành 1 mảng để quét, nhưng đánh dấu lại vị trí bắt đầu của phần tham khảo
        all_chunks = main_chunks + ref_chunks
        ref_start_chunk_index = len(main_chunks)

        all_matches = []
        
        for index, chunk_text in enumerate(all_chunks):
            chunk_segmented = word_tokenize(chunk_text, format="text")
            query_vector = model.encode(chunk_segmented)
            
            # ĐỔI LIMIT = 3 ĐỂ LẤY TOP 3 TÀI LIỆU GIỐNG NHẤT
            search_response = qdrant_client.query_points(
                collection_name="document_chunks", query=query_vector.tolist(), limit=3 
            )
            
            # KIỂM TRA TRÍCH DẪN
            is_quote_flag = check_if_quote(chunk_text)
            
            # [MỚI] 2. KIỂM TRA XEM ĐOẠN NÀY CÓ NẰM TRONG DANH MỤC THAM KHẢO KHÔNG
            is_reference_flag = index >= ref_start_chunk_index
            
            # Gom các nguồn giống vào mảng
            chunk_sources = []
            for point in search_response.points:
                score = point.score
                if score >= 0.50:
                    chunk_sources.append({
                        "source_doc_id": point.payload.get("source_doc_id"),
                        "matched_text": point.payload.get("text"),
                        "similarity_score": round(score, 4),
                        "match_type": "EXACT_MATCH" if score >= 0.85 else "PARAPHRASED"
                    })
            
            if chunk_sources:
                all_matches.append({
                    "chunk_index": index + 1,
                    "student_text": chunk_text,
                    "is_quote": is_quote_flag,
                    "is_reference": is_reference_flag, # [MỚI] 3. Nhét cờ vào payload trả về
                    "sources": chunk_sources
                })

        new_report = ScanReport(
            id=uuid.uuid4(), user_id=current_user.id, submitted_file_name=file.filename,
            status="COMPLETED", total_similarity_score=0.0 
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        # Lưu vào Database (Vòng lặp kép)
        if all_matches:
            for match in all_matches:
                for source in match["sources"]:
                    new_detail = MatchDetail(
                        report_id=new_report.id, 
                        chunk_index=match["chunk_index"],
                        is_quote=match["is_quote"],
                        is_reference=match["is_reference"], # [MỚI] 4. Lưu cờ này xuống Database
                        source_doc_id=source["source_doc_id"],
                        query_text=match["student_text"], 
                        matched_text=source["matched_text"],
                        similarity_score=source["similarity_score"], 
                        match_type=source["match_type"]
                    )
                    db.add(new_detail)
            db.commit()

        return {
            "status": "success", "report_id": new_report.id, "user_email": current_user.email,
            "file_name": file.filename, 
            "total_chunks_scanned": len(all_chunks), # [CẬP NHẬT] Đổi từ chunks thành all_chunks
            "plagiarized_chunks_found": len(all_matches), "matches": all_matches
        }
    except Exception as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@router.get("/history")
async def get_scan_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        reports = db.query(ScanReport)\
            .filter(ScanReport.user_id == current_user.id)\
            .order_by(desc(ScanReport.created_at))\
            .all()
            
        history_list = []
        for report in reports:
            history_list.append({
                "report_id": str(report.id),
                "file_name": report.submitted_file_name,
                "status": report.status,
                "total_similarity_score": report.total_similarity_score,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None
            })
            
        return {
            "status": "success",
            "user_email": current_user.email,
            "total_records": len(history_list),
            "data": history_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy lịch sử: {str(e)}")


@router.get("/history/{report_id}")
async def get_scan_report_detail(
    report_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        report = db.query(ScanReport).filter(
            ScanReport.id == report_id,
            ScanReport.user_id == current_user.id
        ).first()

        if not report:
            raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo hoặc bạn không có quyền xem!")

        matches_db = db.query(MatchDetail).filter(MatchDetail.report_id == report_id).all()

        # THUẬT TOÁN GOM NHÓM DỮ LIỆU TỪ DB THEO CHUNK_INDEX
        grouped_matches = {}
        for m in matches_db:
            if m.chunk_index not in grouped_matches:
                grouped_matches[m.chunk_index] = {
                    "chunk_index": m.chunk_index,
                    "student_text": m.query_text,
                    "is_quote": m.is_quote,
                    "is_reference": m.is_reference, # [MỚI] Kéo cờ từ DB lên
                    "sources": []
                }
            grouped_matches[m.chunk_index]["sources"].append({
                "source_doc_id": m.source_doc_id,
                "matched_text": m.matched_text,
                "similarity_score": m.similarity_score,
                "match_type": m.match_type
            })

        match_list = list(grouped_matches.values())
        match_list.sort(key=lambda x: x["chunk_index"])

        return {
            "status": "success",
            "report_info": {
                "report_id": str(report.id),
                "file_name": report.submitted_file_name,
                "status": report.status,
                "total_similarity_score": report.total_similarity_score,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None
            },
            "total_matches_found": len(match_list),
            "matches": match_list
        }

    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy chi tiết báo cáo: {str(e)}")