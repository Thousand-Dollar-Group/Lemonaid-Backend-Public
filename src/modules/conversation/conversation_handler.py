from fastapi import APIRouter, Depends, Cookie
from .conversation_service import ConversationService
from src.core.models import (
  ConversationCreateRequest,
  ConversationResponse,
  ConversationsResponse,
  MessagesCreateRequest,
  MessagesResponse,
  MessageCreateRequest,
  MessageResponse,
  UploadFilesRequest,
  UploadFilesResponse
)
from .conversation_api_config import (
  CREATE_CONVERSATION_CONFIG,
  READ_CONVERSATIONS_CONFIG,
  CREATE_MESSAGE_CONFIG,
  CREATE_MESSAGES_CONFIG,
  READ_MESSAGES_CONFIG,
  UPLOAD_FILES_CONFIG,
)
from src.shared.jwt_auth import verify_session_token

router = APIRouter()


def get_conversation_service() -> ConversationService:
  return ConversationService()


@router.post("", **CREATE_CONVERSATION_CONFIG)
async def create_conversation(
  request: ConversationCreateRequest,
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
  claim = verify_session_token(access_token)
  return await service.create_conversation(claim["sub"], request.title)


@router.get("", **READ_CONVERSATIONS_CONFIG)
async def read_conversations(
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> ConversationsResponse:
  claim = verify_session_token(access_token)
  return await service.read_conversations(claim["sub"])


@router.post("/{conversation_id}/message", **CREATE_MESSAGE_CONFIG)
async def create_message(
  conversation_id: str,
  request: MessageCreateRequest,
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> MessageResponse:
  claim = verify_session_token(access_token)

  # Convert attachments to dict format if present
  attachments = None
  if request.attachments:
    attachments = [
      {"s3_url": att.s3_url, "filename": att.filename, "file_type": att.file_type}
      for att in request.attachments
    ]

  return await service.create_message(
    claim["sub"],
    conversation_id,
    request.query,
    request.file_description,
    request.resources,
    request.result_text,
    request.email,
    attachments,
  )


@router.post("/{conversation_id}/messages", **CREATE_MESSAGES_CONFIG)
async def create_messages(
  conversation_id: str,
  request: MessagesCreateRequest,
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> MessagesResponse:
  claim = verify_session_token(access_token)
  messages = [
    {
      "query": message.query,
      "file_description": message.file_description,
      "resources": message.resources,
      "result_text": message.result_text,
      "email": message.email,
      "attachments": [
        {"s3_url": att.s3_url, "filename": att.filename, "file_type": att.file_type}
        for att in message.attachments
      ]
      if message.attachments
      else None,
    }
    for message in request.messages
  ]
  return await service.create_messages(claim["sub"], conversation_id, messages)


@router.get("/{conversation_id}/messages", **READ_MESSAGES_CONFIG)
async def read_messages(
  conversation_id: str,
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> MessagesResponse:
  claim = verify_session_token(access_token)
  return await service.read_messages(claim["sub"], conversation_id)

@router.post("/{conversation_id}/attachments/upload-urls", **UPLOAD_FILES_CONFIG)
async def upload_attachments_urls(
  conversation_id: str,
  request: UploadFilesRequest,
  access_token: str = Cookie(include_in_schema=False),
  service: ConversationService = Depends(get_conversation_service),
) -> UploadFilesResponse:
  claim = verify_session_token(access_token)
  return await service.upload_attachments_urls(claim["sub"], conversation_id, request.files)
