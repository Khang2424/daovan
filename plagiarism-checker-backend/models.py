from sqlalchemy import Column, String, Float, ForeignKey, Integer, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from database import Base

# BẢNG NGƯỜI DÙNG
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="STUDENT")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ScanReport(Base):
    __tablename__ = "scan_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Tạm thời để user_id có thể null vì chúng ta chưa làm API Đăng nhập
    user_id = Column(UUID(as_uuid=True), nullable=True) 
    submitted_file_name = Column(String, nullable=False)
    status = Column(String, default="COMPLETED")
    total_similarity_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Mối quan hệ 1-N (1 Report có nhiều MatchDetails)
    matches = relationship("MatchDetail", back_populates="report")

class MatchDetail(Base):
    __tablename__ = "match_details"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("scan_reports.id", ondelete="CASCADE"), nullable=False)
    
    # =========================================================
    # BỔ SUNG 2 CỘT MỚI DÀNH CHO TÍNH NĂNG NHIỀU NGUỒN & BỘ LỌC
    # =========================================================
    chunk_index = Column(Integer, nullable=False) # Lưu vị trí đoạn văn của sinh viên
    is_quote = Column(Boolean, default=False)     # Lưu cờ đánh dấu câu trích dẫn
    is_reference = Column(Boolean, default=False) # Cờ đánh dấu đoạn này nằm trong Danh mục tài liệu tham khảo
    # =========================================================

    source_doc_id = Column(Integer, ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True)
    query_text = Column(Text, nullable=False)
    matched_text = Column(Text, nullable=False)
    similarity_score = Column(Float, nullable=False)
    match_type = Column(String, nullable=False)

    report = relationship("ScanReport", back_populates="matches")

# BẢNG LƯU TRỮ THÔNG TIN ĐỒ ÁN MẪU
class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    sync_status = Column(String, default="INDEXED")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))