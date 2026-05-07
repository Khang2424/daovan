from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import ScanRequest
from auth import get_current_user

# [GỌI 2 PHÒNG BAN KHÁC VÀO LÀM VIỆC]
from services.scan_service import process_document_plagiarism, process_text_plagiarism
from crud.crud_report import create_scan_report

router = APIRouter(prefix="/api/v1/scan", tags=["Scanner"])

@router.post("/text")
async def scan_plagiarism_text_api(request: ScanRequest, current_user: User = Depends(get_current_user)):
    try:
        # Giao cho Lớp Não bộ xử lý
        results = process_text_plagiarism(request.text)
        return {"status": "success", "user_email": current_user.email, "query_text": request.text, "matches": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@router.post("/file")
async def scan_file_plagiarism_api(
    file: UploadFile = File(...),
    scan_mode: str = Form("hybrid"), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    try:
        # 1. Giao cho Não bộ xử lý (Cắt text, chấm AI, gộp đoạn)
        total_chunks, all_matches = await process_document_plagiarism(file, scan_mode)

        # 2. Giao cho Thủ kho lưu trữ Database
        new_report = create_scan_report(db, current_user.id, file.filename, total_chunks, all_matches)

        # 3. Trả kết quả về cho React
        return {
            "status": "success", "report_id": new_report.id, "user_email": current_user.email,
            "file_name": file.filename, "total_chunks_scanned": total_chunks,
            "plagiarized_chunks_found": len(all_matches), "matches": all_matches
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback() 
        error_msg = str(e)
        if "429" in error_msg or "Quota" in error_msg:
            raise HTTPException(status_code=503, detail="Hệ thống AI đã hết lượt quét miễn phí trong phút này. Vui lòng đợi 1 phút rồi thử lại, hoặc dùng chế độ Cơ bản.")
        elif "503" in error_msg:
            raise HTTPException(status_code=503, detail=error_msg)
            
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {error_msg}")