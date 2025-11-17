from fastapi import APIRouter
from .service.summarize import summarize_service
from src.core.models import RecordsRequest

router = APIRouter()


@router.post("")
async def summarize(req: RecordsRequest):
  return await summarize_service(req)
