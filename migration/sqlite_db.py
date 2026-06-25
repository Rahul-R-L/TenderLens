import os
import sqlite3
from config import SQLITE_DB

print("SQLite DB:", SQLITE_DB)
print("Exists:", os.path.exists(SQLITE_DB))

def connect():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_tables():
    conn = connect()

    rows = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """).fetchall()

    conn.close()

    return [r["name"] for r in rows]


def get_table_schema(table_name):
    conn = connect()

    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    conn.close()

    return rows

def fetch_rows(table_name):

    conn = connect()

    rows = conn.execute(
        f'SELECT * FROM "{table_name}"'
    ).fetchall()

    conn.close()

    return rows