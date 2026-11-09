from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db_connection, init_db
from ml_matcher import find_best_teacher

app = FastAPI(
    title="AI-Driven Student-Teacher Matching API",
    version="1.0.0",
    description="Öğrenci sorularını yapay zekâ ile en uygun öğretmenle eşleştiren backend sistemi.",
)


# Uygulama ayağa kalkarken veritabanını otomatik kontrol eder
@app.on_event("startup")
def startup_event():
    init_db()


# Pydantic Veri Doğrulama Modelleri
class QuestionRequest(BaseModel):
    student_id: int
    branch: str
    question_text: str


class TeacherCreate(BaseModel):
    name: str
    email: str
    branch: str
    rating: float = 5.0
    avg_solve_time_min: float = 5.0
    total_solved_count: int = 10
    active_questions_count: int = 0


@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "AI Teacher Matching Backend ve ML Motoru Aktif!",
    }


# 1. Test amaçlı sisteme yeni öğretmen ekleme endpoint'i
@app.post("/teachers/add")
def add_teacher(teacher: TeacherCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Önce users tablosuna ekleyelim
        cursor.execute(
            """
            INSERT INTO users (name, email, role) VALUES (?, ?, 'teacher')
        """,
            (teacher.name, teacher.email),
        )
        teacher_id = cursor.lastrowid

        # Ardından teacher_profiles tablosuna detayları ekleyelim
        cursor.execute(
            """
            INSERT INTO teacher_profiles (teacher_id, branch, rating, avg_solve_time_min, total_solved_count, active_questions_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
            (
                teacher_id,
                teacher.branch,
                teacher.rating,
                teacher.avg_solve_time_min,
                teacher.total_solved_count,
                teacher.active_questions_count,
            ),
        )
        conn.commit()
        return {
            "status": "success",
            "message": f"Öğretmen başarıyla eklendi (ID: {teacher_id})",
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


# 2. Soru sorma ve Yapay Zekâ ile Eşleştirme Endpoint'i
@app.post("/questions/ask")
def ask_question(q: QuestionRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Soruyu veritabanına kaydedelim
    cursor.execute(
        """
        INSERT INTO questions (student_id, branch, question_text, status)
        VALUES (?, ?, ?, 'PENDING')
    """,
        (q.student_id, q.branch, q.question_text),
    )
    question_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # ML Motorunu çağırarak bu branştaki en uygun öğretmeni bulalım
    match_result = find_best_teacher(q.branch)

    if not match_result:
        return {
            "status": "unmatched",
            "question_id": question_id,
            "message": "Şu an bu branşta aktif ve müsait öğretmen bulunamadı. Soru kuyruğa alındı.",
        }

    # Eşleşme başarılıysa eşleşmeyi veritabanına kaydedebiliriz
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO matches (question_id, teacher_id, confidence_score, status)
        VALUES (?, ?, ?, 'PENDING')
    """,
        (
            question_id,
            match_result["teacher_id"],
            match_result["confidence_score"],
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "matched",
        "question_id": question_id,
        "assigned_teacher": match_result["name"],
        "teacher_id": match_result["teacher_id"],
        "confidence_score": round(match_result["confidence_score"], 3),
        "message": "Soru yapay zekâ tarafından başarıyla en uygun öğretmene yönlendirildi!",
    }