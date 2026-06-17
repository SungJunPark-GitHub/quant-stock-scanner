import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
DB_PATH = os.path.join(CACHE_DIR, "stock_cache.db")

CACHE_EXPIRE_MINUTES = 60


def init_cache_db():
    os.makedirs(CACHE_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_history_cache (
            ticker TEXT PRIMARY KEY,
            cached_at TEXT NOT NULL,
            data TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def is_cache_valid(cached_at: str) -> bool:
    cached_time = datetime.fromisoformat(cached_at)
    return datetime.now() - cached_time < timedelta(minutes=CACHE_EXPIRE_MINUTES)


def get_cached_history(ticker: str):
    init_cache_db()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT cached_at, data FROM stock_history_cache WHERE ticker = ?",
        (ticker,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    cached_at, json_data = row

    if not is_cache_valid(cached_at):
        return None

    df = pd.read_json(json_data)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")

    return df


def save_history_cache(ticker: str, df: pd.DataFrame):
    init_cache_db()

    cache_df = df.copy()
    cache_df = cache_df.reset_index()
    cache_df.rename(columns={cache_df.columns[0]: "Date"}, inplace=True)

    json_data = cache_df.to_json(date_format="iso")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO stock_history_cache
        (ticker, cached_at, data)
        VALUES (?, ?, ?)
    """, (
        ticker,
        datetime.now().isoformat(),
        json_data,
    ))

    conn.commit()
    conn.close()