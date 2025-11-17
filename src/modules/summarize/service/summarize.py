from fastapi.responses import JSONResponse
from src.core.models import RecordsRequest
from src.core.config import genai_client, GEMINI_MODEL

import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def summarize_service(req: RecordsRequest):
    try:
        logger.info(f"[RAG Background] Start to generate the background")
        # Combine all query/results into a single prompt
        prompt_content = "\n".join(
            [f"Q: {r.query}\nA: {r.result}" for r in req.records]
        )
        full_prompt = (
            f"You are given a list of query-result pairs.\n"
            f"Summarize the general background or context from them:\n\n{prompt_content}"
        )

        # Send to Gemini
        response = genai_client.models.generate_content(
            contents=[full_prompt],
            model=GEMINI_MODEL
        )

        background_summary = (response.text or "").strip()
        logger.info(f"[RAG Background] Finish to generate the background")
        return {"results": background_summary}

    except Exception as e:
        logger.error(f"[RAG Background] Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
