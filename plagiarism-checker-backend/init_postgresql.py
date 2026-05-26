from database import engine
import models

print("Đang tiến hành tạo các bảng trong PostgreSQL...")
models.Base.metadata.create_all(bind=engine)
print("Hoàn tất!")