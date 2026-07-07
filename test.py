import sqlite3

conn = sqlite3.connect("tenders.db")

print(conn.execute("PRAGMA integrity_check").fetchall())