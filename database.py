import sqlite3

conn = sqlite3.connect("dateme.db", check_same_thread=False)
cur = conn.cursor()

def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        lang TEXT,
        step TEXT
    )
    """)
    conn.commit()
