import sqlite3
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "tutor_hub.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Users Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        referrer_id INTEGER,
        role TEXT DEFAULT 'client',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Leads Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        parent_name TEXT,
        kid_info TEXT,
        contact TEXT,
        track TEXT,
        answers_json TEXT,
        status TEXT DEFAULT 'NEW',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Partners Table (Репетиторы и рекомендатели)
    c.execute("""
    CREATE TABLE IF NOT EXISTS partners (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        contact TEXT,
        ref_code TEXT UNIQUE,
        balance INTEGER DEFAULT 0,
        leads_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, full_name: str, referrer_id: int = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO users (user_id, username, full_name, referrer_id)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        full_name=excluded.full_name
    """, (user_id, username or "", full_name or "", referrer_id))
    conn.commit()
    conn.close()

def create_lead(user_id: int, parent_name: str, kid_info: str, contact: str, track: str, answers: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO leads (user_id, parent_name, kid_info, contact, track, answers_json, status)
    VALUES (?, ?, ?, ?, ?, ?, 'NEW')
    """, (user_id, parent_name, kid_info, contact, track, json.dumps(answers, ensure_ascii=False)))
    lead_id = c.lastrowid
    
    # Check if user was referred by a partner
    c.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row and row['referrer_id']:
        ref_id = row['referrer_id']
        c.execute("UPDATE partners SET leads_count = leads_count + 1 WHERE user_id = ?", (ref_id,))

    conn.commit()
    conn.close()
    return lead_id

def get_leads(status: str = None, limit: int = 15):
    conn = get_connection()
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM leads WHERE status = ? ORDER BY id DESC LIMIT ?", (status, limit))
    else:
        c.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_lead_by_id(lead_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def update_lead_status(lead_id: int, status: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    
    # If status becomes PAID, update partner balance (+2000 rub)
    if status == 'PAID':
        c.execute("SELECT user_id FROM leads WHERE id = ?", (lead_id,))
        lead = c.fetchone()
        if lead:
            c.execute("SELECT referrer_id FROM users WHERE user_id = ?", (lead['user_id'],))
            user = c.fetchone()
            if user and user['referrer_id']:
                c.execute("UPDATE partners SET balance = balance + 2000 WHERE user_id = ?", (user['referrer_id'],))

    conn.commit()
    conn.close()

def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM leads")
    total_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE status = 'NEW'")
    new_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM leads WHERE status = 'PAID'")
    paid_leads = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM partners")
    total_partners = c.fetchone()[0]

    conn.close()
    return {
        "users": total_users,
        "leads": total_leads,
        "new_leads": new_leads,
        "paid_leads": paid_leads,
        "partners": total_partners
    }

def get_or_create_partner(user_id: int, name: str, contact: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM partners WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if row:
        conn.close()
        return dict(row)
    
    ref_code = f"ref_{user_id}"
    c.execute("""
    INSERT INTO partners (user_id, name, contact, ref_code, balance, leads_count)
    VALUES (?, ?, ?, ?, 0, 0)
    """, (user_id, name, contact, ref_code))
    conn.commit()
    c.execute("SELECT * FROM partners WHERE user_id = ?", (user_id,))
    new_row = c.fetchone()
    conn.close()
    return dict(new_row)

def get_all_user_ids():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    ids = [row[0] for row in c.fetchall()]
    conn.close()
    return ids
