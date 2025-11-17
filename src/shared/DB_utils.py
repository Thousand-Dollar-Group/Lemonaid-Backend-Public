import os
import psycopg2
from pgvector.psycopg2 import register_vector
import logging
from typing import List, Optional

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- DB helpers ---
# --- Database Connection ---
def get_conn():
    # Log the connection details being used by the Lambda
    
    logger.debug(f"Attempting to connect to database host='{os.getenv("PG_HOST", "pgvector-db")}', dbname='{os.getenv("PG_DB", "vectordb")}', user='{os.getenv("PG_USER", "postgres")}'")

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("PG_DB", "vectordb"),
            user=os.getenv("PG_USER", "postgres"),
            password=os.getenv("PG_PASSWORD", "postgres"),
            host=os.getenv("PG_HOST", "pgvector-db"),
            port=int(os.getenv("PG_PORT", "5432"))
        )
        logger.debug("Database connection successful.")
        register_vector(conn)
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"DATABASE CONNECTION FAILED: {e}")
        # Re-raise the exception to ensure the application fails clearly
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during DB connection: {e}")
        raise

def run_query(sql: str, params: tuple = None) -> list:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            # Check if the query returns rows before trying to fetch
            if cur.description:
                results = cur.fetchall()
            else:
                results = [] # For queries like INSERT/UPDATE that don't return rows
            conn.commit()
            return results
    finally:
        if conn:
            conn.close()

def retrieve_similar_content(sql: str, params: tuple) -> list[tuple]:
    logger.debug(f"Executing similarity search")
    return run_query(sql, params)

def insert_user(user_id: str, username: str, email: str):
    """
    Insert a new user into the 'users' table using run_query.
    """
    sql = """
    INSERT INTO users (user_id, username, email)
    VALUES (%s, %s, %s)
    ON CONFLICT (email) DO NOTHING
    RETURNING user_id;
    """
    params = (user_id, username, email)
    results = run_query(sql, params)

    if results:
        return results[0][0]
    return None 

def get_user_by_id(user_id: str) -> dict:
    sql = """
    SELECT user_id, username, email, status, created_at, updated_at 
    FROM users 
    WHERE user_id = %s
    """

    params = (user_id,)
    results = run_query(sql, params)

    if not results:
        return {}

    row = results[0]
    return {
        "user_id": row[0],
        "username": row[1],
        "email": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }

def update_user_username(user_id: str, new_username: str):
    """
    Update the username of an existing user in the database.
    """
    sql = """
    SELECT username
    UPDATE users SET username = %s 
    WHERE user_id = %s
    """

    params = (new_username, user_id)
    results = run_query(sql, params)

    if not results:
        return None
    
    return results[0][0]