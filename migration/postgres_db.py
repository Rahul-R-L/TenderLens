import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from config import SUPABASE

def connect():

    return psycopg2.connect(
        host=SUPABASE["host"],
        port=SUPABASE["port"],
        dbname=SUPABASE["dbname"],
        user=SUPABASE["user"],
        password=SUPABASE["password"],
    )

def create_table(conn, table_name, schema_sql):

    cur = conn.cursor()

    sql = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        {schema_sql}
    );
    """

    cur.execute(sql)

    conn.commit()

    cur.close()


def truncate_table(conn, table_name):

    cur = conn.cursor()

    cur.execute(
        f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;'
    )

    conn.commit()

    cur.close()

def insert_rows(conn, table_name, rows):

    if not rows:
        return

    columns = list(rows[0].keys())

    values = [
        tuple(row)
        for row in rows
    ]

    cur = conn.cursor()

    query = sql.SQL("""
        INSERT INTO {} ({})
        VALUES %s
    """).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(
            map(sql.Identifier, columns)
        )
    )

    execute_values(
        cur,
        query.as_string(conn),
        values,
        page_size=1000
    )

    conn.commit()

    cur.close()