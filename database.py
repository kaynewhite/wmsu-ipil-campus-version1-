import sqlite3
import os
import bcrypt

try:
    from config import DB_PATH
except ImportError:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")

os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS users (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT    NOT NULL,
        email        TEXT    UNIQUE NOT NULL,
        password     TEXT    NOT NULL,
        role         TEXT    NOT NULL DEFAULT 'student',
        is_verified  INTEGER DEFAULT 0,
        user_id      TEXT    UNIQUE
    );
    CREATE TABLE IF NOT EXISTS courses (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name  TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS exams (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id     INTEGER NOT NULL,
        teacher_id    INTEGER NOT NULL,
        title         TEXT    NOT NULL,
        timer_minutes INTEGER DEFAULT 60,
        passing_score REAL    DEFAULT 60.0,
        is_active     INTEGER DEFAULT 1,
        FOREIGN KEY(course_id)  REFERENCES courses(id),
        FOREIGN KEY(teacher_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS questions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id        INTEGER NOT NULL,
        question_text  TEXT    NOT NULL,
        type           TEXT    NOT NULL,
        choices        TEXT,
        correct_answer TEXT,
        points         REAL    DEFAULT 1.0,
        FOREIGN KEY(exam_id) REFERENCES exams(id)
    );
    CREATE TABLE IF NOT EXISTS student_answers (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id   INTEGER NOT NULL,
        exam_id      INTEGER NOT NULL,
        question_id  INTEGER NOT NULL,
        answer       TEXT,
        is_correct   INTEGER DEFAULT 0,
        FOREIGN KEY(student_id)  REFERENCES users(id),
        FOREIGN KEY(exam_id)     REFERENCES exams(id),
        FOREIGN KEY(question_id) REFERENCES questions(id)
    );
    CREATE TABLE IF NOT EXISTS results (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id   INTEGER NOT NULL,
        exam_id      INTEGER NOT NULL,
        score        REAL    DEFAULT 0,
        percentage   REAL    DEFAULT 0,
        submitted_at TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(exam_id)    REFERENCES exams(id)
    );
    CREATE TABLE IF NOT EXISTS verification_codes (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id          INTEGER,
        email            TEXT NOT NULL,
        code             TEXT NOT NULL,
        type             TEXT NOT NULL,
        attempts         INTEGER DEFAULT 0,
        expires_at       TEXT    NOT NULL,
        pending_name     TEXT,
        pending_role     TEXT,
        pending_password TEXT,
        pending_user_id  TEXT
    );
    CREATE TABLE IF NOT EXISTS essay_reviews (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        answer_id    INTEGER NOT NULL,
        teacher_id   INTEGER NOT NULL,
        points_given REAL    DEFAULT 0,
        feedback     TEXT,
        reviewed_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(answer_id)  REFERENCES student_answers(id)
    );
"""

def init_db():
    db = get_db()
    db.executescript(_SCHEMA)
    try:
        db.execute("ALTER TABLE users ADD COLUMN user_id TEXT UNIQUE")
        db.commit()
        print("[DB] Migration: user_id column added to users table.")
    except Exception:
        pass
    for column in [
        ('verification_codes', 'pending_name'),
        ('verification_codes', 'pending_role'),
        ('verification_codes', 'pending_password'),
        ('verification_codes', 'pending_user_id'),
    ]:
        try:
            db.execute(f"ALTER TABLE {column[0]} ADD COLUMN {column[1]} TEXT")
            db.commit()
            print(f"[DB] Migration: {column[1]} column added to {column[0]} table.")
        except Exception:
            pass
    cur = db.execute("SELECT id FROM users WHERE email='admin@admin.com'")
    if not cur.fetchone():
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        db.execute(
            """INSERT INTO users (name, email, password, role, is_verified, user_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("Admin", "admin@admin.com", hashed, "admin", 1, "ADMIN-001"),
        )
        db.commit()
        print("[DB] Seeded default admin account.")
    db.close()
    print(f"[DB] Database ready at: {os.path.abspath(DB_PATH)}")

def _ensure_tables_exist():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1 FROM users LIMIT 1")
        conn.close()
    except sqlite3.OperationalError:
        print("[DB] Tables not found — running init_db() automatically...")
        init_db()

_ensure_tables_exist()
