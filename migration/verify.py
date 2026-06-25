import sqlite3

DB_PATH = "../tenders.db"   # Change if required

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get all user tables (ignore SQLite internal tables)
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
""")

tables = cursor.fetchall()

print("-" * 40)
print(f"{'Table':25} {'Rows':>10}")
print("-" * 40)

for (table,) in tables:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    count = cursor.fetchone()[0]
    print(f"{table:25} {count:10,}")

print("-" * 40)

conn.close()