import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc
# [CẬP NHẬT] Thêm SourceDocument để JOIN lấy tên tài liệu tham chiếu
from models import ScanReport, MatchDetail, SourceDocument

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
    """Lấy chi tiết một bài quét kèm tên tài liệu nguồn"""
    report = db.query(ScanReport).filter(ScanReport.id == report_id, ScanReport.user_id == user_id).first()
    if not report: return None, None

    # [CẬP NHẬT] JOIN với SourceDocument để lấy thông tin title và file_path thay vì chỉ lấy ID thô
    results = (
        db.query(
            MatchDetail,
            SourceDocument.title.label("source_title"),
            SourceDocument.file_path.label("source_file_path")
        )
        .outerjoin(SourceDocument, MatchDetail.source_doc_id == SourceDocument.id)
        .filter(MatchDetail.report_id == report_id)
        .order_by(MatchDetail.chunk_index.asc())
        .all()
    )

    # Gắn thêm thuộc tính source_title và source_file_path vào từng bản ghi MatchDetail
    matches = []
    for detail, source_title, source_file_path in results:
        detail.source_title = source_title or f"Tài liệu #{detail.source_doc_id}"
        detail.source_file_path = source_file_path or ""
        matches.append(detail)

    return report, matches