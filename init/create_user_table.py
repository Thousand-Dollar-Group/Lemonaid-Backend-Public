import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
import argparse

parser = argparse.ArgumentParser(description="A script with an overwrite flag.")

# Add a boolean flag. 'action="store_true"' means:
# If the flag is present, set the variable 'overwrite' to True.
# If the flag is absent, the default value (False) is used.
parser.add_argument(
    '--overwrite', 
    action='store_true', 
    help='If present, allows existing files to be overwritten.'
)

args = parser.parse_args()

# Check the value of the flag
if args.overwrite:
    print("⚠️ Overwrite mode is ON. Proceeding with caution.")
    # Add your overwrite logic here
else:
    print("✅ Overwrite mode is OFF. Will not modify existing files.")
    # Add your safe logic here
# Load environment variables
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=os.getenv("PG_DB", "vectordb"),
    user=os.getenv("PG_USER", "postgres"),
    password=os.getenv("PG_PASSWORD", "postgres"),
    host=os.getenv("PG_HOST", "pgvector-db"),
    port=int(os.getenv("PG_PORT", "5432"))
)
cur = conn.cursor()

# Create table schema
if args.overwrite:
    cur.execute("DROP TABLE IF EXISTS users;")
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id UUID PRIMARY KEY,
        username VARCHAR(100),
        email VARCHAR(255) UNIQUE,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT now(),
        updated_at TIMESTAMP DEFAULT now()
    );
""")

register_vector(conn)
conn.commit()  # Commit DDL changes immediately

cur.close()
conn.close()
print("User table created successfully.")
