import os
import uuid
from google.genai.types import GenerateContentConfig
from google import genai
from fastapi import UploadFile, File
from typing import List
import pandas as pd
import logging
import json
from src.core.config import GEMINI_MODEL, GEMINI_API_KEY
# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Define accepted MIME types for documentation files.
ACCEPTED_DOC_TYPES = {
    'application/pdf': '.pdf',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'text/csv': '.csv'
}

async def attachments_parser(
    attachments: List[UploadFile] | None = File(None),
    file_dir: str | None = None
) -> List[str]:
    """
    1. Get the file and query from the attachments
    2. Get the description from Gemini with all the files and content if it's a sheet.
    3.  Return the description (List of String will be split by regular expression )
    """
    try:
        if attachments is None:
            return []
        
        # Initialize the Gemini client
        genai_client = genai.Client(api_key=GEMINI_API_KEY)

        # 1. Get the file and query from the attachments

        # Ensure the file directory exists
        os.makedirs(file_dir, exist_ok=True)

        gemini_files = []
        sheet_contents = []

        for attachment in attachments:
            content, file_type = await attachment_parser(attachment, file_dir)
            logger.debug(f"[Attachments Parser] Content: {content}")
            logger.debug(f"[Attachments Parser] File type: {file_type}")
            if file_type == "sheet":
                sheet_contents.append(content) # Add the sheet content to the list
            elif content is not None:
                gemini_files.append(genai_client.files.get(name=content)) # Add the gemini file to the list
                
        # TODO: the prompt waitting for review and optimization 
        # NEED TO BE REVIEWED
        system_instruction = """
        ## ROLE
        You are a detail-oriented fastener-industry expert whose primary goal is to help user with RFQ (Request for Quote) email building.

        ## INSTRUCTIONS
        For this step, parse every debugrmation from the attachments.
        
        ## OUTPUT
        Return only a JSON array of strings (i.e., list[str]).
        Rules:
        - One string per fastener line item, containing all of that item’s details in source order.
        - If nothing relevant is found, return an empty array `[]`.
        """
        return_content = genai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[*sheet_contents, *gemini_files],
            config=GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema={
                    "type": "array",
                    "items": {"type": "string"}
                },
                temperature=0,
            )
        )

        response_text = return_content.text
        description_list = json.loads(response_text)

        if type(description_list) != list:
            raise RuntimeError("[Attachments Parser] Gemini returned invalid description for the attachment")

        formatted_description = "\n".join(f"- {line}" for line in description_list)
        logger.debug(f"[Attachments Parser] Length of description list: {len(description_list)}") 
        logger.debug(f"[Attachments Parser] Description/BOM:\n{formatted_description[:500]}{'...' if len(formatted_description) > 500 else ''}")

        return description_list


    except Exception as e:
        logger.error(f"[Attachments Parser] Error: {e}")
        raise RuntimeError(f"[Attachments Parser] Error: {e}")


async def attachment_parser( 
    attachment: UploadFile | None = File(None), 
    file_dir: str | None = None
) -> tuple[str, str]:

    """
    Parses and processes an uploaded file attachment, saving it to a file directory.

    Args:
        attachment (UploadFile): The file object to process.
        file_dir (str): The file directory to save files in.
    """

    # Generate a unique filename to prevent collisions
    unique_filename = str(uuid.uuid4())
    base_file_path = os.path.join(file_dir, unique_filename)
    file_ext = None

    # Determine file extension based on content type
    if attachment.content_type in ACCEPTED_DOC_TYPES:
        file_ext = ACCEPTED_DOC_TYPES[attachment.content_type]
    elif attachment.content_type.startswith("image/"):
        # Determine image extension from filename or default to .jpg
        ext = attachment.filename.split('.')[-1] if '.' in attachment.filename else 'jpg'
        file_ext = f'.{ext}'
    else:
        logger.error(f"[Attachment Parser] Unsupported file type: {attachment.content_type}")
        return None, None

    # Construct the full path for the temporary file
    temp_file_path = f"{base_file_path}{file_ext}"

    # First, save the entire file to disk to ensure pandas can read it reliably.
    logger.debug(f"[Attachment Parser] Saving temporary file to: {temp_file_path}")
    contents = attachment.file.read()
    with open(temp_file_path, "wb") as f:
        f.write(contents)
    
    # Get the original file size from the temporary file
    original_size_bytes = os.path.getsize(temp_file_path)
    logger.debug(f"[Attachment Parser] Original file size: {original_size_bytes} bytes")

    is_sheet=False

    # Handle the files based on their type
    if file_ext in ['.xlsx', '.xls']:
        logger.debug(f"[Attachment Parser] Processing Excel file for conversion to JSON...")
        
        try:
            # Read the saved Excel file using pandas
            df = pd.read_excel(temp_file_path, sheet_name=0)
            json_str = df.to_json(orient='records')
            
            logger.debug(f"[Attachment Parser] Converted JSON String Successfully")
            sheet_content="Sheet Content: "+json_str
            is_sheet=True

        except Exception as e:
            logger.error(f"[Attachment Parser] Error converting Excel file: {e}")
            
    else:
        # For all other file types, the file has already been saved.
        logger.debug(f"[Attachment Parser] File processed and saved to: {temp_file_path}")
        # Initialize the Gemini client
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
        gemini_file = genai_client.files.upload(file=temp_file_path)

        if not hasattr(gemini_file, "name"):
            logger.error("[Attachment Parser] Gemini upload failed: no file name returned")
            return None, None

        logger.debug(f"[Attachment Parser] upload file DONE -> {gemini_file.name}")

    if is_sheet:
        return sheet_content, "sheet"
    else:
        return gemini_file.name, "file"
        
    # We should never reach here
    logger.error(f"[Attachment Parser] Unsupported file type: {attachment.content_type}")
    return None, None