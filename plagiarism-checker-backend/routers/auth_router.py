from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate
from auth import get_password_hash, verify_password, create_access_token

# Khởi tạo Router (Nhóm các API liên quan đến Auth)
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký!")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "message": "Đăng ký thành công", "user_id": new_user.id}

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "user_id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}