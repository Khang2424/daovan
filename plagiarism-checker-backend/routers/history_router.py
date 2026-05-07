from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import get_current_user

# Nhúng Lớp Thủ kho (CRUD)
from crud.crud_report import get_user_history, get_report_detail

router = APIRouter(prefix="/api/v1/scan/history", tags=["History"])

@router.get("/")
async def get_scan_history_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Gọi Thủ kho lấy dữ liệu thô
        reports = get_user_history(db, current_user.id)
        
        # 2. Đóng gói lại cho đẹp
        history_list = [{
            "report_id": str(report.id),
            "file_name": report.submitted_file_name,
            "status": report.status,
            "total_similarity_score": report.total_similarity_score,
            "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S") if report.created_at else None
        } for report in reports]
            
        return {
            "status": "success", 
            "user_email": current_user.email,
            "total_records": len(history_list), 
            "data": history_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy lịch sử: {str(e)}")

@router.get("/{report_id}")
async def get_scan_report_detail_api(
    report_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Gọi Thủ kho lấy chi tiết báo cáo và các đoạn vi phạm
        report, matches_db = get_report_detail(db, report_id, current_user.id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo hoặc bạn không có quyền xem!")

        # 2. Thuật toán gom nhóm dữ liệu (Nhóm các nguồn chung vào 1 thẻ chunk_index)
        grouped_matches = {}
        for m in matches_db:
            if m.chunk_index not in grouped_matches:
                grouped_matches[m.chunk_index] = {
                    "chunk_index": m.chunk_index,
                    "student_text": m.query_text,
                    "is_quote": m.is_quote,
                    "is_reference": m.is_reference,
                    "sources": []
                }
            grouped_matches[m.chunk_index]["sources"].append({
                "source_doc_id": m.source_doc_id,
                "matched_text": m.matched_text,
                "similarity_score": m.similarity_score,
                "match_type": m.match_type
            })

        # Sắp xếp lại theo đúng thứ tự đoạn văn
        match_list = list(grouped_matches.values())
        match_list.sort(key=lambda x: x["chunk_index"])

        # 3. Trả về cho Frontend
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