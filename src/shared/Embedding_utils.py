import requests
import logging
from src.core.config import genai_client, GEMINI_API_KEY, API_URL, HEADERS
from typing import Optional, List
from google.genai.types import EmbedContentConfig

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Embeddings ---
def get_embedding(text: str) -> Optional[List[float]]:
    if not API_URL:
        logger.error("MINILM_URL not set")
        return None

    # Loop for the specified number of retries
    for attempt in range(3):
        try:
            r = requests.post(API_URL, headers=HEADERS, json={"inputs": [text]})
            r.raise_for_status()
            return r.json()[0]
        except requests.exceptions.Timeout:
            logger.warning(f"Attempt {attempt + 1} timed out.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Attempt {attempt + 1} failed with a request error: {e}")

        except Exception as e:
            logger.error(f"An unexpected error occurred in get_embedding: {e}")

    logger.error("All retry attempts to get embedding failed.")
    return None

def get_embedding_gemini(text: str) -> Optional[List[float]]:
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set")
        return None
    try:
        r = genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=3072)
        )

        return r.embeddings[0].values
    except requests.RequestException as e:
        status = getattr(e.response, "status_code", "N/A")
        print(f"Error getting embedding: {e}, status code: {status}")
        return None
