import os
import psycopg2
from dotenv import load_dotenv
import time
# Load environment variables
load_dotenv()

while True:
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv("PG_DB", "vectordb"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "postgres"),
            host=os.getenv("PG_HOST", "pgvector-db"),
            port=int(os.getenv("PG_PORT", "5432"))
        )

        cur = conn.cursor()
        cur.execute("SELECT 1;")
        conn.close()
        cur.close()
        print("Database is ready to be used.")
        break
    except psycopg2.OperationalError:
        print("Database is not ready to be used. Waiting for 1 second...")
        time.sleep(1)