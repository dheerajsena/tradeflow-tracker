import sqlite3
import pandas as pd
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "tradeflow.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
    
    # Trades table
    c.execute('''CREATE TABLE IF NOT EXISTS trades
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  date TEXT NOT NULL,
                  event TEXT NOT NULL,
                  spent REAL NOT NULL,
                  earned REAL NOT NULL,
                  pnl REAL NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    hashed = hash_password(password)
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    data = c.fetchone()
    conn.close()
    if data:
        user_id, stored_hash = data
        if check_password(password, stored_hash):
            return user_id, username
    return None, None

def add_trade(user_id, date, event, spent, earned):
    conn = get_connection()
    c = conn.cursor()
    pnl = earned - spent
    c.execute("INSERT INTO trades (user_id, date, event, spent, earned, pnl) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, str(date), event, spent, earned, pnl))
    conn.commit()
    conn.close()

def get_user_trades(user_id):
    conn = get_connection()
    query = "SELECT id, date, event, spent, earned, pnl FROM trades WHERE user_id = ? ORDER BY date DESC"
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    return df

def delete_trade(trade_id, user_id):
    conn = get_connection()
    c = conn.cursor()
    # Ensure user owns the trade
    c.execute("DELETE FROM trades WHERE id = ? AND user_id = ?", (trade_id, user_id))
    conn.commit()
    conn.close()

def get_unique_events(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT event FROM trades WHERE user_id = ? ORDER BY event ASC", (user_id,))
    events = [row[0] for row in c.fetchall()]
    conn.close()
    return events
