import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import os

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")

def run_large_sql_file(path):
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    with open(path, "r", encoding="utf8") as f:
        statement = ""

        for line in f:
            statement += line

            # Execute when a semicolon ends a statement
            if line.strip().endswith(";"):
                try:
                    cur.execute(sql.SQL(statement))
                except Exception as e:
                    print("Error executing statement:\n", statement)
                    print("Error:", e)
                statement = ""

    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    run_large_sql_file("supabase_import.sql")
