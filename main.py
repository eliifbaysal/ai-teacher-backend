from fastapi import FastAPI, Depends, HTTPException, status
import database
import auth
import schemas
from ml_matcher import find_best_teacher

app = FastAPI(title="AI Teacher Matching Backend", version="1.0")

# Uygulama ayağa kalkarken veritabanı tablolarını otomatik oluşturalım
@app.on_event("startup")
def startup_event():
    database.init_db()

@app.get("/")
def read_root():
    return {
        "message": "AI Teacher Matching Backend sistemine hoş geldiniz!",
        "status": "Çalışıyor"
    }


# ==================== AUTHENTICATION (KAYIT VE GİRİŞ) ====================

@app.post("/register")
def register_user(user: schemas.UserCreate):
    """Yeni kullanıcı (öğrenci/öğretmen) kaydı oluşturur."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    # E-posta kontrolü
    existing = cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi ile zaten bir hesap kayıtlı."
        )
    
    hashed_password = auth.get_password_hash(user.password)
    
    cursor.execute(
        "INSERT INTO users (name, email, role, hashed_password) VALUES (?, ?, ?, ?)",
        (user.full_name, user.email, user.role, hashed_password)
    )
    conn.commit()
    user_id = cursor.lastrowid
    
    # Eğer kayıt olan kişi öğretmen ise, teacher_profiles tablosuna da başlangıç kaydı atalım
    if user.role == "teacher":
        cursor.execute(
            "INSERT INTO teacher_profiles (teacher_id, branch, rating, avg_solve_time_min, total_solved_count, active_questions_count, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, "Matematik", 4.8, 4.0, 50, 0, 1)
        )
        conn.commit()
        
    conn.close()
    
    return {
        "user_id": user_id,
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
        "message": "Kayıt başarıyla oluşturuldu!"
    }


@app.post("/login")
def login_user(form_data: schemas.UserLogin):
    """Kullanıcı girişi yapar ve 30 dakika süreli JWT token üretir."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    
    user = cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.email,)).fetchone()
    conn.close()
    
    if not user or not auth.verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz e-posta veya şifre.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 30 dakika süreli token üret
    access_token = auth.create_access_token(data={"sub": user["email"], "role": user["role"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "message": "Giriş başarılı! Oturumunuz 30 dakika boyunca geçerlidir."
    }


# ==================== EŞLEŞTİRME (ML MATCHING) ====================

@app.post("/match-teacher")
def match_teacher(question: schemas.QuestionCreate):
    """ML destekli eşleştirme motorunu çalıştırarak en uygun öğretmeni seçer."""
    best_teacher = find_best_teacher(question.subject)
    
    if not best_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{question.subject}' branşında o an aktif uygun öğretmen bulunamadı.")
        
        
    return {
        "status": "Başarılı",
        "matched_subject": question.subject,
        "matched_topic": question.topic,
        "selected_teacher": best_teacher
    }