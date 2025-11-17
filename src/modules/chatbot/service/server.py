#!/usr/bin/env python
# coding: utf-8

# Standard library imports
import json as jsonlib
from typing import List, Optional
import logging

# Third-party imports
from fastapi import File, Form, UploadFile
from google.genai.types import GenerateContentConfig
from fastapi.responses import JSONResponse
from src.core.config import genai_client, GEMINI_MODEL  

# Local application imports
from ..lib.attachment_parser import attachments_parser
from ..lib.similarity_retriever import get_context_and_ifi
from src.core.models import ChatbotReq, ChatbotRes, ChatbotResult
from src.shared.File_utils import read_file_text
from ..lib.display_formatter import render_histories

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def agent_service(
  attachments: Optional[List[UploadFile]] = File(None),
  chatbotReq: Optional[str] = Form(None)
  # At least one of attachments or chatbotReq must be provided; enforce in function body
):
  """
  1. Receive ChatReq
  2. Pass ALL attachments into attachment_parser to get attachment description (List of string) for multiple fastener
  3. For each fastener and user's query, retrieve IFI(md) and Content (string) by applying sliding window cosine similarity on vector DB
  4. Attach all doc and ask Gemini
  """
  try:
    # 1. Receive ChatReq
    # Convert Form of chatbotReq into JSON
    if isinstance(chatbotReq, dict):
      request_data = chatbotReq
    else:
      # If it's a string, attempt to load it from JSON
      request_data = jsonlib.loads(chatbotReq)
      logger.debug(f"[RAG chatbot] ChatbotReq: {request_data}")

    request_obj = ChatbotReq(**request_data)

    # At least one of attachments or query is required
    if not attachments and not request_obj.query:
      logger.error(
        "[RAG chatbot] Error: At least one of attachments or query is required"
      )
      raise ValueError(
        "[RAG chatbot] Error: At least one of attachments or query is required"
      )

    logger.debug("\n=== [RAG chatbot] ===")
    logger.debug(f"Query: {request_obj.query}")
    logger.debug(
      f"Background: {request_obj.background if request_obj.background else '(none)'}"
    )
    logger.debug("Histories:")
    if request_obj.histories:
      for i, h in enumerate(request_obj.histories, 1):
        logger.debug(f"  {i}. Q: {h.query}")
        logger.debug(f"     FileDesc: {h.file_description or '(none)'}")
        logger.debug(f"     Resources: {', '.join(h.resources) or '(none)'}")
        logger.debug(f"     Result: {h.result.text or '(none)'}")
    else:
      logger.debug("  (no previous histories)")
    logger.debug("=========================\n")

    # 2. Pass all attachments into file_parser to get description for multiple fastner
    fasteners_description: List[str] = await attachments_parser(
      attachments, file_dir="/tmp"
    )  # List of string
    joined_description = (
      "\n".join(fasteners_description) if fasteners_description else ""
    )
    logger.debug(
      f"[RAG chatbot] Fasteners description: {joined_description[:300]}{'...' if len(joined_description) > 300 else ''}"
    )

    # 3. For each fastener, retrieve IFI(md) and Content (string) by applying sliding window cosine similarity on vector DB
    all_similar_docs: List[tuple[str, str]] = []
    unique_similar_docs = set()
    for single_description in fasteners_description + [request_obj.query]:
      if single_description.strip() == "":
        continue
      similar_docs = await get_context_and_ifi(
        single_description, top_n=3
      )  # List of tuple (content, ifi_file_name)
      logger.debug(f"[RAG chatbot] Length of similar docs: {len(similar_docs)}")
      for content, ifi_file_name in similar_docs:
        if (
          ifi_file_name not in unique_similar_docs
        ):  # WARNING: if there are duplicate ifi_file_name, the content will be overwritten
          unique_similar_docs.add(ifi_file_name)
          all_similar_docs.append((content, ifi_file_name))
          logger.debug(
            f"[RAG chatbot] Similar doc: {content[:100]}{'...' if len(content) > 100 else ''}"
          )
          logger.debug(f"[RAG chatbot] Similar doc: {ifi_file_name}")
          logger.debug("=========================\n")

    logger.debug(f"[RAG chatbot] Length of all_similar_docs: {len(all_similar_docs)}")

    # 4. Attach all doc and ask Gemini
    return ChatbotRes(
      query=request_obj.query,
      file_description=joined_description,  # all fasteners description
      resources=[
        ifi_file_name for _, ifi_file_name in all_similar_docs
      ],  # all ifi_file_name
      result=ChatbotResult(
        **ask_gemini(all_similar_docs, request_obj, joined_description)
      ),
    )

  except Exception as e:
    logger.error(f"[RAG chatbot] Error: {e}")
    return JSONResponse(status_code=500, content={"error": str(e)})


# --- Send the prompt to Gemini
def ask_gemini(
  all_similar_docs: List[tuple[str, str]],
  request_obj: ChatbotReq,
  joined_description: str,
) -> str:
  """
  1. Get the query, fasteners_description, histories from the request object
  2. Render the histories into a readable text
  3. Generate the prompt with the hidden prompt, query, description, histories, and similar docs
  4. Send the prompt to Gemini
  5. Return the response
  """

  try:
    background = ", \n\n".join(request_obj.background) if request_obj.background else ""
    query = request_obj.query.strip()
    histories = request_obj.histories or []
    histories_text = render_histories(histories)
    similar_docs_text = ""
    for _, ifi_file_name in all_similar_docs:
      similar_docs = read_file_text(ifi_file_name)
      similar_docs_text += similar_docs
      similar_docs_text += "\n\n"
    similar_docs_text = similar_docs_text.strip()

    # --- Hidden/system prompt
    system_instruction = f"""
        ## ROLE
        You are a detail-oriented fastener-industry expert whose primary goal is to help users with RFQ (Request for Quote) email building.

        ## INSTRUCTIONS
        - Observe the user's language in the `## QUERY` section. Your response should match the user's language and style, especially when following explicit instructions.
        - Use ONLY the information provided in the prompt sections.
        - First, answer the user's questions (based solely on the provided sections).
        - Then confirm whether the user wants to proceed with a quote for the mentioned fastener(s).
        - If the user has not already explicitly asked for a quote, confirm whether they want to proceed.
        - If the user confirms or has already asked for a quote, follow the `## WORKFLOW` below.

        ## WORKFLOW
        1) Consistency check
           Check for contradictions across the sections `## BACKGROUND`, `## CONTEXT`, `## HISTORY`, and `## QUERY` (if any are provided).
           - If you find contradictions, ask the user to clarify **before** proceeding.

        2) Build the RFQ email
           Once (a) the user confirms they wish to quote (or if they have already asked for a quote) and (b) contradictions are resolved, compose the RFQ email.
           - Generate the email body by populating the `## TEMPLATE` below. The generated body must be plain text (no markdown).
           - Use angle-bracket placeholders like <THIS> for any missing information.
           - Keep the exact section titles and order from the template.
           - If a field's value is not provided in the context, omit that entire line from the item details (do NOT invent values).
           - If the user specifies the material as zinc plating, append Cr3+ to it.
           - Treat each “item” as a separate sellable unit. If an item is a kit, list its contents as line items under that item's description.
           - Ensure units (e.g., pcs, kg) are included where provided.

        ### CRITICAL TEMPLATE RULE ###
        The section starting with "SUPPLIER TO PROVIDE" is a static, literal block. It MUST be copied into the final email exactly as it appears in the template below. DO NOT substitute any data into the placeholders (e.g., `<ITEM_LABEL>`, `<VALID_DAYS>`) within this specific section. Preserve them exactly as they are.

        ## TEMPLATE

        

        ## BACKGROUND
        {background or "(none)"}

        ## OUTPUT
        You MUST respond with a single JSON object only (no prose, no code fences).
        Schema:
        {{
            "text": string,
            "email": null | {{
                "to": string[],
                "cc": string[],
                "bcc": string[],
                "subject": string,
                "body": string
            }}
        }}
        Rules:
        - Always include the "text" and "email" keys exactly as named above.
        - When no email should be generated (including when asking clarifying questions or awaiting user confirmation), set "email" to null.
        - When an email is generated, set "email" to an object as defined above; use empty arrays/empty strings inside the object when a field has no value.
        - When an email is generated, keep "subject" an empty string; "to", "cc", and "bcc" an empty array.
        - Do not add extra keys or metadata.
        - Output must be valid JSON (UTF-8, no trailing commas).
        """

    prompt = f"""
        ## CONTEXT
        {similar_docs_text or "(none)"}

        ## HISTORY
        {histories_text or "(none)"}

        ## ATTACHMENT
        {joined_description or "(none)"}

        ## QUERY
        {query}
        """

    logger.info(f"[RAG chatbot] Prompt: {prompt}")
    response = genai_client.models.generate_content(
      model=GEMINI_MODEL,
      contents=[prompt],
      config=GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema={
          "type": "object",
          "required": ["text", "email"],
          "properties": {
            "text": {"type": "string"},
            "email": {
              "anyOf": [
                {
                  "type": "object",
                  "required": ["to", "cc", "bcc", "subject", "body"],
                  "properties": {
                    "to": {"type": "array", "items": {"type": "string"}, "default": []},
                    "cc": {"type": "array", "items": {"type": "string"}, "default": []},
                    "bcc": {
                      "type": "array",
                      "items": {"type": "string"},
                      "default": [],
                    },
                    "subject": {"type": "string", "default": ""},
                    "body": {"type": "string"},
                  },
                },
                {"type": "null"},
              ]
            },
          },
        },
        temperature=0,
      ),
    )

    result = response.text.strip()
    logger.info(f"[RAG chatbot] Gemini response: {result}")
    return jsonlib.loads(result)

  except Exception as e:
    logger.error(f"[RAG chatbot] Error: {e}")
    raise RuntimeError(f"[RAG chatbot] Error: {e}")