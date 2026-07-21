import sqlite3

SOURCE_DB = "all_tenders.db"
DEST_DB = "tenders.db"

TABLES = ["tenders", "boq_items", "boq_headings"]

src = sqlite3.connect(SOURCE_DB)
src.row_factory = sqlite3.Row

dst = sqlite3.connect(DEST_DB)

src_cur = src.cursor()
dst_cur = dst.cursor()

# --------------------------------------------------
# Create required tables
# --------------------------------------------------
for table in TABLES:
    create_sql = src_cur.execute("""
        SELECT sql
        FROM sqlite_master
        WHERE type='table'
        AND name=?
    """, (table,)).fetchone()[0]

    dst_cur.execute(f"DROP TABLE IF EXISTS {table}")
    dst_cur.execute(create_sql)

dst.commit()

# --------------------------------------------------
# Get active tenders
# --------------------------------------------------
active_tenders = src_cur.execute("""
    SELECT *
    FROM tenders
    WHERE date(bid_end_iso) >= date('now', 'localtime')
""").fetchall()

print(f"Active tenders found : {len(active_tenders)}")

boq_items_count = 0
boq_heading_count = 0

for tender in active_tenders:

    tender_id = tender["tender_id"]

    # ----------------------------
    # Copy tender
    # ----------------------------
    cols = tender.keys()
    placeholders = ",".join(["?"] * len(cols))

    dst_cur.execute(
        f"""
        INSERT INTO tenders ({",".join(cols)})
        VALUES ({placeholders})
        """,
        tuple(tender)
    )

    # ----------------------------
    # Copy BOQ Items
    # ----------------------------
    items = src_cur.execute("""
        SELECT *
        FROM boq_items
        WHERE tender_id=?
    """, (tender_id,)).fetchall()

    for item in items:
        cols = item.keys()
        placeholders = ",".join(["?"] * len(cols))

        dst_cur.execute(
            f"""
            INSERT INTO boq_items ({",".join(cols)})
            VALUES ({placeholders})
            """,
            tuple(item)
        )

    boq_items_count += len(items)

    # ----------------------------
    # Copy BOQ Headings
    # ----------------------------
    headings = src_cur.execute("""
        SELECT *
        FROM boq_headings
        WHERE tender_id=?
    """, (tender_id,)).fetchall()

    for heading in headings:
        cols = heading.keys()
        placeholders = ",".join(["?"] * len(cols))

        dst_cur.execute(
            f"""
            INSERT INTO boq_headings ({",".join(cols)})
            VALUES ({placeholders})
            """,
            tuple(heading)
        )

    boq_heading_count += len(headings)

dst.commit()

print("\nMigration completed successfully.")
print("-----------------------------------")
print(f"Tenders copied      : {len(active_tenders)}")
print(f"BOQ Headings copied : {boq_heading_count}")
print(f"BOQ Items copied    : {boq_items_count}")

src.close()
dst.close()