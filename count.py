import sqlite3

conn = sqlite3.connect("tenders.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM tenders")
count = cursor.fetchone()[0]

print(f"Total tenders: {count}")

conn.close()