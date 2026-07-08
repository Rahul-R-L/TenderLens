import sqlite3
from pprint import pprint

conn = sqlite3.connect("tenders.db")
conn.row_factory = sqlite3.Row

row = conn.execute(
    "SELECT * FROM boq_headings LIMIT 1"
).fetchone()

pprint(dict(row))