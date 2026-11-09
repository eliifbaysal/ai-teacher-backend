from datetime import datetime
import sqlite3

DB_NAME = "campus_prod.db"


def get_db_connection():
    """SQLite / Cloudflare D1 veritabanına bağlantı açar ve dict dönecek şekilde ayarlar."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Verileri sütun adlarıyla sözlük gibi çekebilmek için
    return conn


def init_db():
    """Proje ilk ayağa kalktığında gerekli tabloları oluşturan fonksiyon."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Kullanıcılar Tablosu (Öğrenci ve Öğretmenler)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'teacher')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # 2. Öğretmen Profil ve Performans Metrikleri Tablosu (ML için kritik)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS teacher_profiles (
            teacher_id INTEGER PRIMARY KEY,
            branch TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1, -- 1: Çevrimiçi, 0: Çevrimdışı
            rating REAL DEFAULT 5.0,
            avg_solve_time_min REAL DEFAULT 5.0,
            total_solved_count INTEGER DEFAULT 0,
            active_questions_count INTEGER DEFAULT 0, -- Load Balancing için anlık yük
            FOREIGN KEY (teacher_id) REFERENCES users (user_id) ON DELETE CASCADE
        )
    """
    )

    # 3. Sorular Tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            branch TEXT NOT NULL,
            question_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'MATCHED', 'SOLVED', 'TIMEOUT', 'UNMATCHED')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users (user_id)
        )
    """
    )

    # 4. Eşleşme ve Atama Tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            confidence_score REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'TIMEOUT', 'COMPLETED')),
            retry_count INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions (question_id),
            FOREIGN KEY (teacher_id) REFERENCES users (user_id)
        )
    """
    )

    conn.commit()
    conn.close()
    print("Veritabanı ve tablolar başarıyla oluşturuldu!")


# Dosya doğrudan çalıştırılırsa veritabanını otomatik oluştursun
if __name__ == "__main__":
    init_db()
#yorum
