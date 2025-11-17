from typing import List, Dict, Any
from src.shared.DB_utils import run_query
from uuid import UUID


class ConversationRepository:
  @staticmethod
  def insert_conversation(user_id: str, title: str):
    """
    Insert a new conversation into the 'conversations' table.
    """
    sql = """
        INSERT INTO conversations (user_id, title)
        VALUES (%s, %s)
        RETURNING *;
        """
    params = (user_id, title)
    results = run_query(sql, params)
    # print(results)

    if not results:
      return {}

    row = results[0]
    return {
      "conversation_id": row[0],
      "user_id": row[1],
      "title": row[2],
      "created_at": row[3],
      "updated_at": row[4],
    }

  @staticmethod
  def get_conversations_by_user(user_id: str):
    """
    Return all conversations for a given user_id.
    Returns a list of dicts
    """
    sql = """
        SELECT *
        FROM conversations
        WHERE user_id = %s
        ORDER BY updated_at DESC;
        """
    params = (user_id,)
    results = run_query(sql, params)

    if not results:
      return []

    conversations = []
    for row in results:
      conversations.append(
        {
          "conversation_id": row[0],
          "user_id": row[1],
          "title": row[2],
          "created_at": row[3],
          "updated_at": row[4],
        }
      )
    return conversations

  @staticmethod
  def insert_message(
    conversation_id: str,
    query: str,
    file_description: str | None,
    resources: List[str],
    result_text: str,
    email: str | None,
  ):
    """
    Insert a new message into the 'messages' table.
    """
    sql = """
        INSERT INTO messages (conversation_id, query, file_description, resources, result_text, email)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
        """
    params = (conversation_id, query, file_description, resources, result_text, email)
    results = run_query(sql, params)
    # print(results)

    if not results:
      return {}

    row = results[0]
    return {
      "message_id": row[0],
      "conversation_id": row[1],
      "query": row[2],
      "file_description": row[3],
      "resources": row[4],
      "result_text": row[5],
      "email": row[6],
      "created_at": row[7],
      "updated_at": row[8],
    }

  @staticmethod
  def insert_messages(conversation_id: str, messages: List[Dict[str, Any]]):
    if not messages:
      return []
    params = [
      (
        conversation_id,
        msg.get("query"),
        msg.get("file_description"),
        msg.get("resources") if msg.get("resources") is not None else [],
        msg.get("result_text"),
        msg.get("email"),
      )
      for msg in messages
    ]
    flat_params = [item for tup in params for item in tup]

    sql = f"""
        INSERT INTO messages (conversation_id, query, file_description, resources, result_text, email)
        VALUES {",".join(["(%s,%s,%s,%s,%s,%s)"] * len(params))}
        RETURNING *;
        """
    results = run_query(sql, flat_params)

    if not results:
      return []

    out = []
    for row in results:
      out.append(
        {
          "message_id": row[0],
          "conversation_id": row[1],
          "query": row[2],
          "file_description": row[3],
          "resources": row[4],
          "result_text": row[5],
          "email": row[6],
          "created_at": row[7],
          "updated_at": row[8],
        }
      )
    return out

  @staticmethod
  def insert_attachments(message_id: str, attachments: List[Dict[str, Any]]):
    """
    Insert attachments for a message into the 'attachments' table.
    """
    if not attachments:
      return []

    params = [
      (message_id, att.get("s3_url"), att.get("filename"), att.get("file_type"))
      for att in attachments
    ]
    flat_params = [item for tup in params for item in tup]

    sql = f"""
        INSERT INTO attachments (message_id, s3_url, filename, file_type)
        VALUES {",".join(["(%s,%s,%s,%s)"] * len(params))}
        RETURNING *;
        """
    results = run_query(sql, flat_params)

    if not results:
      return []

    out = []
    for row in results:
      out.append(
        {
          "attachment_id": row[0],
          "message_id": row[1],
          "s3_url": row[2],
          "filename": row[3],
          "file_type": row[4],
          "created_at": row[5],
        }
      )
    return out

  @staticmethod
  def get_messages_by_conversation(conversation_id: str):
    """
    Get all messages for a conversation with their attachments.
    Returns messages with attachments nested as a list.
    """
    sql = """
        SELECT
            m.*,
            COALESCE(
                json_agg(to_jsonb(a) ORDER BY a.created_at ASC)
                FILTER (WHERE a.attachment_id IS NOT NULL),
                '[]'
            ) as attachments
        FROM messages m
        LEFT JOIN attachments a ON m.message_id = a.message_id
        WHERE m.conversation_id = %s
        GROUP BY m.message_id
        ORDER BY m.created_at ASC;
        """
    params = (conversation_id,)
    results = run_query(sql, params)

    if not results:
      return []

    messages = []
    for row in results:
      messages.append(
        {
          "message_id": row[0],
          "conversation_id": row[1],
          "query": row[2],
          "file_description": row[3],
          "resources": row[4],
          "result_text": row[5],
          "email": row[6],
          "created_at": row[7],
          "updated_at": row[8],
          "attachments": row[9],
        }
      )
    return messages

  @staticmethod
  def check_conversation_ownership(user_id: str, conversation_id: str) -> str:
    """
    Check the ownership of a conversation.

    Returns:
        "not_found"    -> conversation_id doesn't exist in DB
        "not_owner"    -> conversation exists but belongs to another user
        "ok"           -> conversation belongs to the given user
    """
    sql = """
        SELECT user_id
        FROM conversations
        WHERE conversation_id = %s;
        """
    result = run_query(sql, (conversation_id,))

    if not result:
      return "not_found"

    db_user_id = result[0][0]

    print(user_id)
    print(db_user_id)

    if UUID(db_user_id) != UUID(user_id):
      print("here")
      return "not_owner"

    return "ok"
