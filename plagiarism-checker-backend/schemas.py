from pydantic import BaseModel

class ScanRequest(BaseModel):
    text: str

class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "STUDENT"