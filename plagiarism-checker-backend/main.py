from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import auth_router, scan_router, history_router 

# Tạo bảng DB nếu chưa có
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Plagiarism Checker API",
    description="Hệ thống kiểm tra đạo văn sử dụng Vector Embeddings",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Mở cửa cho ReactJS Vite
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Routes (APIs) từ thư mục routers
app.include_router(auth_router.router)
app.include_router(scan_router.router)

# [MỚI] 2. Đăng ký Router lịch sử vào App
app.include_router(history_router.router) 

# API Kiểm tra trạng thái server
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "message": "Server đang chạy bình thường"}