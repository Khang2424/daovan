import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc
from underthesea import word_tokenize

from database import get_db
from models import User, ScanReport, MatchDetail
from schemas import ScanRequest
from auth import get_current_user
from services import model, qdrant_client, extract_text_from_file, chunk_text_sliding_window, check_if_quote, split_main_and_references, evaluate_plagiarism_with_gemini, merge_overlapping_text

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
    scan_mode: str = Form("hybrid"), # [MỚI] Nhận chế độ quét từ Frontend (mặc định là hybrid) 
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
                    source_text_from_db = point.payload.get("text")
                    
                    # =======================================================
                    # [MỚI] LOGIC 3 CHẾ ĐỘ QUÉT THEO LỰA CHỌN CỦA USER
                    # =======================================================
                    final_score = round(score, 4)
                    final_match_type = "SAFE"

                    if scan_mode == "offline":
                        # Chế độ 1: Nhanh, mộc mạc bằng thuật toán cũ
                        final_match_type = "EXACT_MATCH" if score >= 0.85 else "PARAPHRASED"
                        
                    elif scan_mode == "hybrid":
                        if score >= 0.85:
                            final_match_type = "EXACT_MATCH"
                        else:
                            try:
                                gemini_result = evaluate_plagiarism_with_gemini(chunk_text, source_text_from_db)
                                time.sleep(4) # Tạm dừng 4 giây để tránh bị Google block (Giới hạn 15 req/min)
                                
                                # Lấy kết quả một cách an toàn, mặc định là SAFE nếu không có
                                final_match_type = gemini_result.get("match_type", "SAFE")
                                
                            except Exception as e:
                                # Chỉ chạy vào đây nếu services.py thực sự ném lỗi (hết token, rớt mạng)
                                error_msg = str(e)
                                if "429" in error_msg or "Quota" in error_msg:
                                    friendly_msg = "Hệ thống AI đã hết lượt quét miễn phí trong phút này. Vui lòng đợi 1 phút rồi thử lại, hoặc dùng chế độ Cơ bản."
                                else:
                                    friendly_msg = "Hệ thống AI gặp sự cố kết nối. Vui lòng thử lại sau."
                                    
                                raise HTTPException(
                                    status_code=503, 
                                    detail=friendly_msg
                                )
                                
                    elif scan_mode == "online":
                        try:
                            gemini_result = evaluate_plagiarism_with_gemini(chunk_text, source_text_from_db)
                            time.sleep(4) # Tạm dừng 4 giây để tránh bị Google block (Giới hạn 15 req/min)
                            
                            final_score = gemini_result.get("similarity_score", round(score, 4))
                            final_match_type = gemini_result.get("match_type", "SAFE")
                            
                        except Exception as e:
                                error_msg = str(e)
                                if "429" in error_msg or "Quota" in error_msg:
                                    friendly_msg = "Hệ thống AI đã hết lượt quét miễn phí trong phút này. Vui lòng đợi 1 phút rồi thử lại, hoặc dùng chế độ Cơ bản."
                                else:
                                    friendly_msg = "Hệ thống AI gặp sự cố kết nối. Vui lòng thử lại sau."
                                    
                                raise HTTPException(
                                    status_code=503, 
                                    detail=friendly_msg
                                )

                    # [MỚI] CHỈ LƯU VÀO KẾT QUẢ NẾU NÓ KHÔNG PHẢI LÀ "SAFE"
                    if final_match_type != "SAFE":
                        chunk_sources.append({
                            "source_doc_id": point.payload.get("source_doc_id"),
                            "matched_text": source_text_from_db,
                            "similarity_score": final_score,
                            "match_type": final_match_type
                        })
            
            if chunk_sources:
                all_matches.append({
                    "chunk_index": index + 1,
                    "student_text": chunk_text,
                    "is_quote": is_quote_flag,
                    "is_reference": is_reference_flag,
                    "sources": chunk_sources
                })

        # ========================================================
        # [MỚI] THUẬT TOÁN GỘP ĐOẠN VĂN BỊ LẶP (MERGE OVERLAPPING)
        # ========================================================
        merged_matches = []
        for match in all_matches:
            if not match["sources"]: 
                continue
                
            if not merged_matches:
                merged_matches.append(match)
                continue
                
            prev_match = merged_matches[-1]
            
            # ------------------------------------------------------------------------
            # [SIÊU CẤP] THUẬT TOÁN ĐÔN NGUỒN CHUNG (SHARED SOURCE PROMOTION)
            # Nếu 2 đoạn liên tiếp, tìm xem chúng có chung tài liệu nguồn trong Top 3 không
            # ------------------------------------------------------------------------
            if match["chunk_index"] == prev_match["chunk_index"] + 1:
                prev_source_ids = [s["source_doc_id"] for s in prev_match["sources"]]
                
                for curr_source in match["sources"]:
                    if curr_source["source_doc_id"] in prev_source_ids:
                        # Đưa nguồn chung lên vị trí Top 1 của đoạn hiện tại (match)
                        match["sources"].remove(curr_source)
                        match["sources"].insert(0, curr_source)
                        
                        # Đưa nguồn chung tương ứng lên vị trí Top 1 của đoạn trước đó (prev_match)
                        for ps in prev_match["sources"]:
                            if ps["source_doc_id"] == curr_source["source_doc_id"]:
                                prev_match["sources"].remove(ps)
                                prev_match["sources"].insert(0, ps)
                                break
                        break # Chỉ cần tìm thấy 1 nguồn chung là đủ, thoát vòng lặp đôn nguồn
            # ------------------------------------------------------------------------
            
            # Lấy ID của nguồn tham chiếu Top 1 (sau khi đã được đôn lên nếu có)
            curr_source_id = match["sources"][0]["source_doc_id"]
            prev_source_id = prev_match["sources"][0]["source_doc_id"]
            
            # ĐIỀU KIỆN GỘP:
            if (match["chunk_index"] == prev_match["chunk_index"] + 1 and 
                curr_source_id == prev_source_id and
                match["is_quote"] == prev_match["is_quote"] and
                match["is_reference"] == prev_match["is_reference"] and
                match["sources"][0]["match_type"] == prev_match["sources"][0]["match_type"]):
                
                # Tiến hành hàn Text của sinh viên
                prev_match["student_text"] = merge_overlapping_text(prev_match["student_text"], match["student_text"])
                
                # Tiến hành hàn Text của nguồn gốc
                prev_match["sources"][0]["matched_text"] = merge_overlapping_text(
                    prev_match["sources"][0]["matched_text"], 
                    match["sources"][0]["matched_text"]
                )
                
                # Cập nhật index để kéo dài chuỗi gộp (nếu có đoạn 5, 6 giống nhau)
                prev_match["chunk_index"] = match["chunk_index"]
            else:
                merged_matches.append(match)

        # Gán lại mảng đã gọt dũa sạch sẽ
        all_matches = merged_matches
        # ========================================================

        # LƯU VÀO DATABASE 
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
    except HTTPException as http_ex:
        # [MỚI] Nếu là lỗi 503 do ta chủ động ném ra, thì giữ nguyên nó và đẩy về cho Frontend
        db.rollback()
        raise http_ex 
        
    except Exception as e:
        # Lỗi hệ thống thực sự (database, server...) thì mới bọc thành 500
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

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