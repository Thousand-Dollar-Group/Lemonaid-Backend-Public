import os
from typing import Optional
import logging
from src.core.config import IFI_DIR

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- File reader ---
def read_file_text(filename: Optional[str]) -> str:
    if not filename:
        return ""
        
    path = os.path.join(IFI_DIR, f"{filename}.md")
    if not os.path.exists(path):
        logger.warning(f"[Missing parsed file]: {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
