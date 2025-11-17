import os
import ast
import psycopg2
import pandas as pd
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


cur.execute("""
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_name = 'documents'
    );
""")
table_exists = cur.fetchone()[0]
print(f"Documents table exists: {table_exists}")

if table_exists:
    print("Documents table already exists. Skipping ingestion.")
    cur.close()
    conn.close()
    exit()


# Directory containing your CSV files
DATA_DIR = "./src/data"

# Collect all CSV files in the directory
CSV_FILES = [
    os.path.join(DATA_DIR, f)
    for f in os.listdir(DATA_DIR)
    if f.endswith(".csv")
]

print(f"Found {len(CSV_FILES)} CSV files: {CSV_FILES}")

# Create table schema
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
conn.commit()

if args.overwrite:
    cur.execute("DROP TABLE IF EXISTS documents;")
    conn.commit()

cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id SERIAL PRIMARY KEY,
        content TEXT,
        embedding VECTOR,
        IFI_file_name TEXT
    );
""")

register_vector(conn)
conn.commit()  # Commit DDL changes immediately

for file in CSV_FILES:
    df = pd.read_csv(file)
    print(f"Reading {file} ({len(df)} rows)")
    
    for _, row in df.iterrows():
        content = str(row["content"])
        
        # Parse embedding string to list of floats (assumed format: "[0.1, 0.2, ...]")
        embedding = ast.literal_eval(row["embedding"])
        ifi_file_name = str(row["IFI_file_name"])

        cur.execute(
            "INSERT INTO documents (content, embedding, IFI_file_name) VALUES (%s, %s, %s);",
            (content, embedding, ifi_file_name)
        )

conn.commit()
cur.close()
conn.close()
print("All CSV data inserted successfully.")
