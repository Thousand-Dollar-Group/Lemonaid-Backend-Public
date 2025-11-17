from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socket as _s
from src.modules.auth import api as auth_api
from src.modules.chatbot import api as chat_api
from src.modules.summarize import api as sum_api
from src.modules.conversation import conversation_handler

# Force IPv4 to avoid AF_INET6 issues seen in Lambda/VPC
_s.has_ipv6 = False

# OpenAPI/Swagger documentation for each group
openapi_tags = [
  {
    "name": "Auth",
    "description": "Authentication endpoints",
  },
  {
    "name": "Chatbot",
    "description": "Core chat experiences",
  },
  {
    "name": "Background",
    "description": "",
  },
  {
    "name": "Conversation",
    "description": "Conversation threads",
  },
]

app = FastAPI(redirect_slashes=True, openapi_tags=openapi_tags)
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(chat_api.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(sum_api.router, prefix="/api/background", tags=["Background"])
app.include_router(
  conversation_handler.router, prefix="/api/conversation", tags=["Conversation"]
)
app.include_router(auth_api.router, prefix="/auth", tags=["Auth"])
