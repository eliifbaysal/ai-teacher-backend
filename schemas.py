from pydantic import BaseModel
from typing import Optional

# --- KULLANICI ŞEMALARI (Auth / Kayıt / Giriş) ---
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str  # "student" veya "teacher"

class UserLogin(BaseModel):
    email: str
    password: str

# --- ÖĞRETMEN PROFİL ŞEMALARI ---
class TeacherProfileCreate(BaseModel):
    user_id: int
    subject: str
    rating: float = 5.0
    current_load: int = 0
    performance_score: float = 0.8

# --- SORU VE EŞLEŞTİRME ŞEMALARI ---
class QuestionCreate(BaseModel):
    student_id: int
    subject: str
    difficulty: int = 3  # 1 ile 5 arası zorluk