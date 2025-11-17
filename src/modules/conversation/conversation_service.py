import logging
from typing import List, Dict, Optional, Any
import json
import uuid
from fastapi import HTTPException

from .conversation_repository import ConversationRepository
from src.core.models import (
  ConversationResponse,
  ConversationsResponse,
  MessageResponse,
  MessagesResponse,
  AttachmentResponse,
  UploadFilesRequest,
  UploadFilesResponse,
  UploadFilesInfo,
)
from src.shared.S3_utils import get_presigned_url

class ConversationService:
  async def create_conversation(self, user_id: str, title: str) -> ConversationResponse:
    result = ConversationRepository.insert_conversation(user_id, title)

    resp = ConversationResponse(
      conversation_id=result["conversation_id"],
      title=result["title"],
      created_at=result["created_at"].isoformat(),
      updated_at=result["updated_at"].isoformat(),
    )
    return resp

  async def read_conversations(self, user_id: str) -> ConversationsResponse:
    results = ConversationRepository.get_conversations_by_user(user_id)

    count = 0
    conversations = []
    for res in results:
      conv = ConversationResponse(
        conversation_id=res["conversation_id"],
        title=res["title"],
        created_at=res["created_at"].isoformat(),
        updated_at=res["updated_at"].isoformat(),
      )
      conversations.append(conv)
      count += 1

    resp = ConversationsResponse(conversations=conversations, count=count)
    return resp

  async def create_message(
    self,
    user_id: str,
    conversation_id: str,
    query: str,
    file_description: Optional[str],
    resources: Optional[List[str]],
    result_text: str,
    email: Optional[str],
    attachments: Optional[List[Dict[str, str]]],
  ) -> MessageResponse:
    status = ConversationRepository.check_conversation_ownership(
      user_id, conversation_id
    )
    if status == "not_found":
      raise HTTPException(status_code=404, detail="Conversation not found")
    elif status == "not_owner":
      raise HTTPException(status_code=403, detail="Access denied")

    message = [
      {
        "query": query,
        "file_description": file_description,
        "resources": resources,
        "result_text": result_text,
        "email": email,
      }
    ]
    result = ConversationRepository.insert_messages(conversation_id, message)

    # Insert attachments if provided
    attachment_responses = []
    if attachments:
      attachment_results = ConversationRepository.insert_attachments(
        result[0]["message_id"], attachments
      )
      for att in attachment_results:
        attachment_responses.append(
          AttachmentResponse(**{**att, "created_at": att["created_at"].isoformat()})
        )
      result[0]["attachments"] = attachment_responses

    email_data = result[0]["email"]
    if isinstance(email_data, dict):
      email_data = json.dumps(email_data)
    result[0]["email"] = email_data
    result[0]["created_at"] = result[0]["created_at"].isoformat()
    result[0]["updated_at"] = result[0]["updated_at"].isoformat()

    return MessageResponse(**result[0])

  async def create_messages(
    self, user_id: str, conversation_id: str, messages: List[Dict[str, Any]]
  ) -> MessagesResponse:
    status = ConversationRepository.check_conversation_ownership(
      user_id, conversation_id
    )
    if status == "not_found":
      raise HTTPException(status_code=404, detail="Conversation not found")
    elif status == "not_owner":
      raise HTTPException(status_code=403, detail="Access denied")

    results = ConversationRepository.insert_messages(conversation_id, messages)

    count = 0
    message_responses = []
    for result in results:
      # Insert attachments if provided for this message
      attachment_responses = []
      # Find the corresponding message from input to get attachments
      original_msg = messages[count] if count < len(messages) else {}
      if original_msg.get("attachments"):
        attachment_results = ConversationRepository.insert_attachments(
          result["message_id"], original_msg["attachments"]
        )
        for att in attachment_results:
          attachment_responses.append(
            AttachmentResponse(**{**att, "created_at": att["created_at"].isoformat()})
          )
      
      email_data = result["email"]
      if isinstance(email_data, dict):
        email_data = json.dumps(email_data)
    
      msg = MessageResponse(
        message_id=result['message_id'],
        conversation_id=result['conversation_id'],
        query =result['query'],
        file_description= result['file_description'],
        resources= result['resources'],
        result_text= result['result_text'],
        email= email_data,
        attachments=attachment_responses,
        created_at=result["created_at"].isoformat(),
        updated_at=result["updated_at"].isoformat(),
      )
      message_responses.append(msg)
      count += 1

    resp = MessagesResponse(messages=message_responses, count=count)
    return resp

  async def read_messages(self, user_id: str, conversation_id: str) -> MessagesResponse:
    # print(conversation_id)
    status = ConversationRepository.check_conversation_ownership(
      user_id, conversation_id
    )
    if status == "not_found":
      raise HTTPException(status_code=404, detail="Conversation not found")
    elif status == "not_owner":
      raise HTTPException(status_code=403, detail="Access denied")

    results = ConversationRepository.get_messages_by_conversation(conversation_id)

    count = 0
    messages = []
    for result in results:
      # Parse attachments from JSON
      attachment_responses = []
      if result.get("attachments"):
        for att in result["attachments"]:
          S3_URL_PREFIX = 'https://lemonaid-attachments-bucket.s3.amazonaws.com/'
          s3_key = att['s3_url'].replace(S3_URL_PREFIX, '', 1)
          att["s3_url"] = get_presigned_url('get_object', 'lemonaid-attachments-bucket', s3_key, 3600, ContentType=att['file_type']) # 1 hr expiration 
          print(att["s3_url"])
          attachment_responses.append(AttachmentResponse(**att))
        result["attachments"] = attachment_responses

      email_data = result["email"]
      if isinstance(email_data, dict):
        email_data = json.dumps(email_data)
      result["email"] = email_data
      result["created_at"] = result["created_at"].isoformat()
      result["updated_at"] = result["updated_at"].isoformat()
      messages.append(MessageResponse(**result))
      count += 1

    return MessagesResponse(messages=messages, count=count)

  async def upload_attachments_urls(self, user_id: str, conversation_id: str, request: UploadFilesRequest) -> UploadFilesResponse:
    status = ConversationRepository.check_conversation_ownership(user_id, conversation_id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Conversation not found")
    elif status == "not_owner":
        raise HTTPException(status_code=403, detail="Access denied")
    
    uploads_list = []
    for file in request:
        try:
          unique_id = str(uuid.uuid4())
          s3_key = f"attachments/user-{user_id}/conv-{conversation_id}/{unique_id}-{file.filename}"
          url = get_presigned_url(
                'put_object', 
                'lemonaid-attachments-bucket', 
                s3_key, 
                900, 
                # This keyword must be accepted by your wrapper and passed to Boto3's Params for signing
                ContentType=file.file_type 
            ) 

          uploads_list.append(
                UploadFilesInfo(
                    filename=file.filename, 
                    upload_url=url, 
                    s3_key=s3_key  # Clean key for database storage
                )
          )
        except Exception as e:
          logging.error(f"Failed to generate upload URL for {file.filename}: {e}")
          pass

    if not uploads_list:
        raise HTTPException(status_code=500, detail="Failed to generate upload URLs")

    return UploadFilesResponse(files=uploads_list)