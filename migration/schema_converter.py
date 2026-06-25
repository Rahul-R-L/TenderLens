TYPE_MAP = {
    "INTEGER": "INTEGER",
    "TEXT": "TEXT",
    "REAL": "DOUBLE PRECISION",
    "BLOB": "BYTEA",
    "NUMERIC": "NUMERIC"
}

SPECIAL_TYPES = {
    ("tenders", "tender_value"): "TEXT",
    ("tenders", "tender_value_num"): "DOUBLE PRECISION",
}
def sqlite_to_postgres(table_name, schema):

    columns = []

    for col in schema:

        key = (table_name, col["name"])

        if key in SPECIAL_TYPES:
            col_type = SPECIAL_TYPES[key]
        else:
            col_type = TYPE_MAP.get(
                col["type"].upper(),
                "TEXT"
            )

        sql = f'"{col["name"]}" {col_type}'

        if col["pk"]:
            sql += " PRIMARY KEY"

        if col["notnull"]:
            sql += " NOT NULL"

        if col["dflt_value"] is not None:
            sql += f" DEFAULT {col['dflt_value']}"

        columns.append(sql)

    return ",\n".join(columns)