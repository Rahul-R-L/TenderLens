import sqlite3
from pprint import pprint

conn = sqlite3.connect("tenders.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("TENDERS")
cur.execute("SELECT * FROM tenders LIMIT 1")
row = cur.fetchone()
if row:
    pprint(dict(row))

print("\nBOQ_ITEM")
cur.execute("SELECT * FROM boq_items LIMIT 1")
row = cur.fetchone()
if row:
    pprint(dict(row))

conn.close()