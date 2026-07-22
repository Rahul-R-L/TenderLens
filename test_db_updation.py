import sqlite3

conn = sqlite3.connect("all_tenders.db")
cur = conn.cursor()

tables = cur.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
ORDER BY name
""").fetchall()

for t in tables:
    print(t[0])

conn.close()