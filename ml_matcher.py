import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from database import get_db_connection

MODEL_PATH = "matcher_model.joblib"


def train_or_load_model():
    """Eğer önceden eğitilmiş model yoksa basit bir RandomForest modeli eğitir ve kaydeder."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)

    # Eğitim için örnek sentetik veri (Gerçek projede geçmiş başarılı eşleşme verileri kullanılır)
    # Özellikler: [rating, avg_solve_time_min, total_solved_count, active_questions_count]
    X_train = [
        [4.9, 3.0, 150, 0],
        [4.2, 8.0, 40, 2],
        [3.5, 12.0, 10, 4],
        [5.0, 2.0, 300, 0],
        [4.7, 5.0, 90, 1],
    ]
    # Etiket: 1 (İdeal eşleşme), 0 (Zayıf eşleşme)
    y_train = [1, 0, 0, 1, 1]

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    joblib.dump(model, MODEL_PATH)
    return model


def find_best_teacher(branch: str):
    """Verilen branştaki aktif öğretmenleri çeker, Pandas ile hazırlar ve ML modeli ile skorlar."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Sadece ilgili branşta ve çevrimiçi (is_active = 1) olan öğretmenleri çekiyoruz
    query = """
        SELECT t.teacher_id, t.branch, t.rating, t.avg_solve_time_min, 
               t.total_solved_count, t.active_questions_count, u.name
        FROM teacher_profiles t
        JOIN users u ON t.teacher_id = u.user_id
        WHERE t.branch = ? AND t.is_active = 1
    """
    teachers_data = cursor.execute(query, (branch,)).fetchall()
    conn.close()

    if not teachers_data:
        return None  # Uygun öğretmen bulunamadı

    # 2. Verileri Pandas DataFrame'e aktarıyoruz (Feature Engineering)
    df = pd.DataFrame([dict(row) for row in teachers_data])

    # 3. Model için özellik matrisini (Feature Matrix) oluşturuyoruz
    X_live = df[
        [
            "rating",
            "avg_solve_time_min",
            "total_solved_count",
            "active_questions_count",
        ]
    ]

    # 4. Modeli yüklüyoruz ve olasılık tahminlerini alıyoruz
    model = train_or_load_model()
    probabilities = model.predict_proba(X_live)[
        :, 1
    ]  # İdeal eşleşme sınıfı olasılığı

    df["confidence_score"] = probabilities

    # 5. Dinamik Yük Dengeleme (Load Balancing) Cezası:
    # Aktif soru başına skordan %10 düşerek yoğun öğretmenlerin boğulmasını önlüyoruz
    df["adjusted_score"] = df["confidence_score"] - (
        df["active_questions_count"] * 0.10
    )

    # 6. En yüksek düzeltilmiş skora sahip öğretmeni seçiyoruz
    best_teacher = df.loc[df["adjusted_score"].idxmax()]

    return {
        "teacher_id": int(best_teacher["teacher_id"]),
        "name": best_teacher["name"],
        "confidence_score": float(best_teacher["adjusted_score"]),
    }
# yorum