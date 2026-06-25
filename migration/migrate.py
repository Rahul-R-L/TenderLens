import time
from postgres_db import (
    connect,
    create_table,
    truncate_table,
    insert_rows
)

from sqlite_db import (
    get_tables,
    get_table_schema,
    fetch_rows
)

from schema_converter import sqlite_to_postgres


conn = connect()

for table in get_tables():

    if table == "sqlite_sequence":
        continue

    print(f"\nProcessing {table}")

    schema = get_table_schema(table)
    schema_sql = sqlite_to_postgres(table, schema)

    create_table(
        conn,
        table,
        schema_sql
    )
    start = time.time()

    truncate_table(conn, table)

    rows = fetch_rows(table)

    print(f"Copying {len(rows)} rows...")

    insert_rows(
        conn,
        table,
        rows
    )
    print(
        f"Finished in {time.time()-start:.2f} sec"
    )
conn.close()

print("Done.")