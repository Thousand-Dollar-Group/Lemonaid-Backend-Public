from fastapi import APIRouter, File, Form, UploadFile
from typing import List, Optional
from .service.server import agent_service
from src.core.models import ChatbotRes

router = APIRouter()


@router.post("")
async def agent_router(
  attachments: Optional[List[UploadFile]] = File(None),
  chatbotReq: Optional[str] = Form(None),
) -> ChatbotRes:
  return await agent_service(attachments, chatbotReq)
