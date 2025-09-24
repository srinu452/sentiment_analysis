import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = Path("app.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        con.commit()

def create_user(email: str, password: str):
    pw_hash = generate_password_hash(password)
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("INSERT INTO users (email, password_hash) VALUES (?, ?);",
                    (email.lower(), pw_hash))
        con.commit()

def find_user(email: str):
    with get_conn() as con:
        cur = con.cursor()
        cur.execute("SELECT id, email, password_hash FROM users WHERE email = ?;", (email.lower(),))
        row = cur.fetchone()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "password_hash": row[2]}

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)
