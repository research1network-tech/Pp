# database.py
import sqlite3
import json
import os
from datetime import datetime
from config import DATABASE

# التأكد من وجود المجلد
os.makedirs(os.path.dirname(DATABASE), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # جدول حسابات Telegram (للنشر)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        session TEXT NOT NULL,
        phone TEXT NOT NULL,
        is_active INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # جدول المنشورات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        has_media INTEGER DEFAULT 0,
        media_type TEXT,
        media_file_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # جدول المجموعات المخزنة مؤقتاً
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        group_title TEXT NOT NULL,
        group_username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, account_id, group_id),
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(account_id) REFERENCES telegram_accounts(id)
    )
    """)
    
    # جدول إعدادات النشر
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS publish_settings (
        user_id INTEGER PRIMARY KEY,
        delay_seconds INTEGER DEFAULT 5,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # جدول الجدولة
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        scheduled_time TIMESTAMP NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(account_id) REFERENCES telegram_accounts(id)
    )
    """)
    
    # جدول الحملات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        post_ids TEXT,
        account_ids TEXT,
        status TEXT DEFAULT 'draft',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # جدول سجل العمليات
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        campaign_id INTEGER,
        account_id INTEGER,
        post_id INTEGER,
        group_id INTEGER,
        status TEXT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    conn.commit()
    conn.close()

# ========== دوال المستخدمين ==========
def create_user(username, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

# ========== دوال حسابات Telegram ==========
def add_telegram_account(user_id, session, phone):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE telegram_accounts SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute(
        "INSERT INTO telegram_accounts (user_id, session, phone, is_active) VALUES (?, ?, ?, 1)",
        (user_id, session, phone)
    )
    conn.commit()
    acc_id = cursor.lastrowid
    conn.close()
    return acc_id

def get_telegram_accounts(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM telegram_accounts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    accounts = cursor.fetchall()
    conn.close()
    return accounts

def get_active_account(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM telegram_accounts WHERE user_id = ? AND is_active = 1", (user_id,))
    account = cursor.fetchone()
    conn.close()
    return account

def set_active_account(user_id, account_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE telegram_accounts SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute("UPDATE telegram_accounts SET is_active = 1 WHERE id = ? AND user_id = ?", (account_id, user_id))
    conn.commit()
    conn.close()

def delete_account(user_id, account_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM telegram_accounts WHERE id = ? AND user_id = ?", (account_id, user_id))
    conn.commit()
    conn.close()

# ========== دوال المنشورات ==========
def create_post(user_id, content, media_type=None, media_file_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, content, has_media, media_type, media_file_id) VALUES (?, ?, ?, ?, ?)",
        (user_id, content, 1 if media_file_id else 0, media_type, media_file_id)
    )
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def get_posts(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    posts = cursor.fetchall()
    conn.close()
    return posts

def delete_post(user_id, post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id = ? AND user_id = ?", (post_id, user_id))
    conn.commit()
    conn.close()

# ========== دوال المجموعات ==========
def save_groups_cache(user_id, account_id, groups):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups_cache WHERE user_id = ? AND account_id = ?", (user_id, account_id))
    for g in groups:
        cursor.execute(
            "INSERT INTO groups_cache (user_id, account_id, group_id, group_title, group_username) VALUES (?, ?, ?, ?, ?)",
            (user_id, account_id, g['id'], g['title'], g.get('username'))
        )
    conn.commit()
    conn.close()

def get_cached_groups(user_id, account_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM groups_cache WHERE user_id = ? AND account_id = ? ORDER BY group_title",
        (user_id, account_id)
    )
    groups = cursor.fetchall()
    conn.close()
    return groups

# ========== دوال الإعدادات ==========
def get_publish_settings(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT delay_seconds FROM publish_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['delay_seconds'] if row else 5

def set_publish_settings(user_id, delay_seconds):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO publish_settings (user_id, delay_seconds) VALUES (?, ?)",
        (user_id, delay_seconds)
    )
    conn.commit()
    conn.close()

# ========== دوال الجدولة ==========
def add_schedule(user_id, account_id, scheduled_time):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO schedules (user_id, account_id, scheduled_time) VALUES (?, ?, ?)",
        (user_id, account_id, scheduled_time)
    )
    conn.commit()
    sch_id = cursor.lastrowid
    conn.close()
    return sch_id

def get_schedules(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE user_id = ? AND status = 'pending' ORDER BY scheduled_time", (user_id,))
    schedules = cursor.fetchall()
    conn.close()
    return schedules

def cancel_schedule(schedule_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE schedules SET status = 'cancelled' WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

def mark_schedule_executed(schedule_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE schedules SET status = 'executed' WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()

# ========== دوال الحملات ==========
def create_campaign(user_id, name, post_ids, account_ids):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO campaigns (user_id, name, post_ids, account_ids) VALUES (?, ?, ?, ?)",
        (user_id, name, json.dumps(post_ids), json.dumps(account_ids))
    )
    conn.commit()
    camp_id = cursor.lastrowid
    conn.close()
    return camp_id

def get_campaigns(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    campaigns = cursor.fetchall()
    conn.close()
    return campaigns

def delete_campaign(campaign_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))
    conn.commit()
    conn.close()

# ========== دوال سجل العمليات ==========
def log_operation(user_id, campaign_id, account_id, post_id, group_id, status, error_message=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO operation_logs (user_id, campaign_id, account_id, post_id, group_id, status, error_message) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, campaign_id, account_id, post_id, group_id, status, error_message)
    )
    conn.commit()
    conn.close()

def get_operation_logs(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM operation_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    )
    logs = cursor.fetchall()
    conn.close()
    return logs
