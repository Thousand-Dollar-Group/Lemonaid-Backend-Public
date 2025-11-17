import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Embeddings
API_URL = os.getenv("MINILM_URL")
HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# IFI_DIR
IFI_DIR = os.getenv("IFI_DIR", "./src/IFI_Table_Files")

# Cognito
COGNITO_DOMAIN = os.environ.get("COGNITO_DOMAIN")
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET")
COGNITO_REGION = os.environ.get("COGNITO_REGION")
USER_POOL_ID = os.environ.get("USER_POOL_ID")
APP_FRONTEND_URL = os.environ.get("APP_FRONTEND_URL")
