import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models import ScanReport, MatchDetail

def create_scan_report(db: Session, user_id: str, file_name: str, total_chunks: int, all_matches: list):
    """Lưu kết quả quét tổng thể và chi tiết từng đoạn văn vào Database"""
    new_report = ScanReport(
        id=uuid.uuid4(), user_id=user_id, submitted_file_name=file_name,
        status="COMPLETED", total_similarity_score=0.0 
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    if all_matches:
        for match in all_matches:
            for source in match["sources"]:
                new_detail = MatchDetail(
                    report_id=new_report.id, chunk_index=match["chunk_index"],
                    is_quote=match["is_quote"], is_reference=match["is_reference"],
                    source_doc_id=source["source_doc_id"], query_text=match["student_text"], 
                    matched_text=source["matched_text"], similarity_score=source["similarity_score"], 
                    match_type=source["match_type"]
                )
                db.add(new_detail)
        db.commit()
    return new_report

def get_user_history(db: Session, user_id: str):
    """Lấy danh sách lịch sử quét của user"""
    return db.query(ScanReport).filter(ScanReport.user_id == user_id).order_by(desc(ScanReport.created_at)).all()

def get_report_detail(db: Session, report_id: str, user_id: str):
    """Lấy chi tiết một bài quét"""
    report = db.query(ScanReport).filter(ScanReport.id == report_id, ScanReport.user_id == user_id).first()
    if not report: return None, None
    matches = db.query(MatchDetail).filter(MatchDetail.report_id == report_id).all()
    return report, matches