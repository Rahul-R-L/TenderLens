from dotenv import load_dotenv
import os

load_dotenv()

SQLITE_DB = os.getenv("SQLITE_DB")

SUPABASE = {
    "host": os.getenv("SUPABASE_HOST"),
    "port": int(os.getenv("SUPABASE_PORT")),
    "dbname": os.getenv("SUPABASE_DATABASE"),
    "user": os.getenv("SUPABASE_USER"),
    "password": os.getenv("SUPABASE_PASSWORD"),
}