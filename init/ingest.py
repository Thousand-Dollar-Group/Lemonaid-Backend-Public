import os
import requests
import psycopg2
import numpy as np
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pgvector.psycopg2 import register_vector

# Load environment variables
load_dotenv()

import warnings
from PyPDF2 import PdfReader

# 1. Load and process PDFs in batches
pdf_dir = "./src/sources"
all_texts = []

# Verify directory exists
if not os.path.exists(pdf_dir):
    raise FileNotFoundError(f"Directory '{pdf_dir}' not found")

for filename in os.listdir(pdf_dir):
   if filename.endswith(".pdf"):
        pdf_path = os.path.join(pdf_dir, filename)
        print(pdf_path)
        
        # Add PDF validation
        try:

            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                if len(reader.pages) == 0:
                    print(f"⚠️ Warning: {filename} has no readable pages")
        except Exception as e:
            print(f"❌ Error validating {filename}: {str(e)}")
            continue  # Skip corrupted files
        
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        for doc in documents:
            doc.page_content = doc.page_content.replace('\x00', '')
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,  # Reduced for token limits
            chunk_overlap=1000
        )
        split_docs = splitter.split_documents(documents)
        texts = [doc.page_content for doc in split_docs]
        all_texts.extend(texts)

print(all_texts)


# 2. Generate embeddings in batches
API_URL = os.environ.get("MINILM_URL")
headers = {"Authorization": f"Bearer {os.environ['HUGGINGFACE_API_TOKEN']}"}
embeddings = []
batch_size = 32  # API maximum batch size

for i in range(0, len(all_texts), batch_size):
    batch = all_texts[i:i+batch_size]
    payload = {
        "inputs": batch,
        "parameters": {"truncation": True}  # Explicit truncation
    }

    print(i)
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        embeddings_batch = response.json()
        embeddings.extend(embeddings_batch)
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed for batch {i//batch_size}: {e}")
        # Optional: Implement retry logic here
        # break  # Uncomment to stop on first error

print(f"Generated {len(embeddings)} embeddings from {len(all_texts)} chunks")

# 3. Connect to PostgreSQL and store embeddings
try:
    conn = psycopg2.connect(
        dbname="vectordb",
        user="postgres",
        password="postgres",
        host="pgvector-db",
        port=5432
    )
    print("Hi1")

    cur = conn.cursor()
    print("Hi2")
    
    # Enable pgvector and create table
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("DROP TABLE IF EXISTS documents;")
    cur.execute("""
        CREATE TABLE documents (
            id SERIAL PRIMARY KEY,
            content TEXT,
            embedding VECTOR(384)
        );
    """)
    conn.commit()  # Commit DDL changes immediately

    register_vector(conn)
    print("Hi3")
    
    # Insert documents and embeddings
    for content, emb in zip(all_texts, embeddings):
        embedding_list = emb if isinstance(emb, list) else emb.tolist()
        cur.execute(
            "INSERT INTO documents (content, embedding) VALUES (%s, %s);",
            (content, embedding_list)
        )
        print(content)
    conn.commit()  # Commit all inserts after loop

    # Create HNSW index for faster similarity search
    cur.execute("CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);")
    print("Created HNSW index")
    conn.commit()

except psycopg2.OperationalError as e:
    print(f"Database connection failed: {e}")
    print("Ensure PostgreSQL is running and credentials are correct")
except Exception as e:
    print(f"Error: {e}")
    # Rollback if any error occurs during operations
    if 'conn' in locals():
        conn.rollback()
finally:
    # Only attempt to fetch if connection exists
    if 'cur' in locals() and 'conn' in locals():
        try:
            cur.execute("SELECT id, content, embedding FROM documents ORDER BY id;")
            all_data = cur.fetchall()
            
            # Print all embeddings
            # for doc_id, content, embedding in all_data:
            #     print(f"ID: {doc_id}\nContent: {content}\nEmbedding: {embedding}\n---")
        except Exception as e:
            print(f"Error during fetch: {e}")
    
    # Cleanup resources
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
