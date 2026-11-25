import sqlite3
from datetime import datetime
from config import DATABASE_PATH

def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            service_name TEXT,
            service_price INTEGER,
            date_time TEXT,
            phone TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'new'
        )
    """)
    conn.commit()
    conn.close()

def add_booking(user_id: int, username: str, full_name: str, service_name: str, service_price: int, date_time: str, phone: str):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (user_id, username, full_name, service_name, service_price, date_time, phone, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
    """, (user_id, username or "", full_name, service_name, service_price, date_time, phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def get_all_bookings(limit: int = 10):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, phone, service_name, service_price, date_time, status, created_at FROM bookings ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_stats():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(service_price), 0) FROM bookings")
    total_count, total_sum = cursor.fetchone()
    conn.close()
    return total_count, total_sum
