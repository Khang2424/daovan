import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Tải các biến môi trường từ file .env lên hệ thống
load_dotenv()

# Lấy đường dẫn DB từ file .env (Không còn lộ mật khẩu ở đây nữa)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Khởi tạo Engine (Động cơ kết nối)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Khởi tạo Session (Phiên làm việc với DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class để các Models (Bảng) kế thừa
Base = declarative_base()

# Hàm tạo dependency cho FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()