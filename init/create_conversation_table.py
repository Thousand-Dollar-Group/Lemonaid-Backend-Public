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
  "--overwrite",
  action="store_true",
  help="If present, allows existing files to be overwritten.",
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
with psycopg2.connect(
  dbname=os.getenv("PG_DB", "vectordb"),
  user=os.getenv("PG_USER", "postgres"),
  password=os.getenv("PG_PASSWORD", "postgres"),
  host=os.getenv("PG_HOST", "pgvector-db"),
  port=int(os.getenv("PG_PORT", "5432")),
) as conn:
  with conn.cursor() as cur:
    # Create pgvector extension if not exists
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Drop existing database objects if overwrite flag is set
    if args.overwrite:
      # Drop functions
      cur.execute("DROP FUNCTION IF EXISTS update_conversation_timestamp CASCADE;")
      cur.execute("DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;")

      # Drop tables and all dependent objects
      cur.execute("DROP TABLE IF EXISTS attachments CASCADE;")
      cur.execute("DROP TABLE IF EXISTS messages CASCADE;")
      cur.execute("DROP TABLE IF EXISTS conversations CASCADE;")

    # Create tables
    cur.execute("""
      CREATE TABLE IF NOT EXISTS conversations (
        conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(user_id),
        title VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
      );
    """)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS messages (
        message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
        query TEXT,
        file_description TEXT,
        resources TEXT[] NOT NULL DEFAULT '{}',
        result_text TEXT NOT NULL,
        email JSONB,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
      );
    """)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS attachments (
        attachment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        message_id UUID NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
        s3_url TEXT NOT NULL,
        filename VARCHAR(255) NOT NULL,
        file_type VARCHAR(100) NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT clock_timestamp()
      );
    """)

    # Create composite index on common columns for faster lookups
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);"
    )
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at ASC);"
    )
    cur.execute(
      "CREATE INDEX IF NOT EXISTS idx_attachments_message ON attachments(message_id, created_at ASC);"
    )

    # Create functions to automatically update the updated_at timestamp
    cur.execute("""
      CREATE OR REPLACE FUNCTION update_updated_at_column()
      RETURNS TRIGGER AS $$
      BEGIN
        NEW.updated_at = clock_timestamp();
        RETURN NEW;
      END;
      $$ LANGUAGE plpgsql;
    """)
    cur.execute("""
      CREATE OR REPLACE FUNCTION update_conversation_timestamp()
      RETURNS TRIGGER AS $$
      BEGIN
        IF TG_OP = 'DELETE' THEN
          UPDATE conversations
          SET updated_at = clock_timestamp()
          WHERE conversation_id = OLD.conversation_id;
          RETURN OLD;
        ELSE
          UPDATE conversations
          SET updated_at = clock_timestamp()
          WHERE conversation_id = NEW.conversation_id;
          RETURN NEW;
        END IF;
      END;
      $$ LANGUAGE plpgsql;
    """)

    # Create trigger to update messages.updated_at on row updates
    cur.execute("DROP TRIGGER IF EXISTS update_messages_updated_at ON messages;")
    cur.execute("""
      CREATE TRIGGER update_messages_updated_at
        BEFORE UPDATE ON messages
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create trigger to update conversation timestamp on message insert/update/delete
    cur.execute(
      "DROP TRIGGER IF EXISTS update_conversation_on_message_change ON messages;"
    )
    cur.execute("""
      CREATE TRIGGER update_conversation_on_message_change
        AFTER INSERT OR UPDATE OR DELETE ON messages
        FOR EACH ROW
        EXECUTE FUNCTION update_conversation_timestamp();
    """)

    # Create trigger to update conversations.updated_at on row updates
    cur.execute(
      "DROP TRIGGER IF EXISTS update_conversations_updated_at ON conversations;"
    )
    cur.execute("""
      CREATE TRIGGER update_conversations_updated_at
        BEFORE UPDATE ON conversations
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

  # Register pgvector extension for vector operations
  register_vector(conn)

  # Explicit commit
  conn.commit()

print("Conversation table created successfully.")
