from fastapi import APIRouter, Request, Cookie
from typing import Optional
from .service.auth import auth_callback, auth_post_user, auth_logout
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/callback")
async def auth_router(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    return await auth_callback(request, code, error)


@router.post("/user")
async def auth_post_user_router(request: Request, id_token: str = Cookie(default=None)):
    res = await auth_post_user(request)
    return JSONResponse(content=res)

@router.post("/logout")
async def auth_logout_router():
    return await auth_logout()