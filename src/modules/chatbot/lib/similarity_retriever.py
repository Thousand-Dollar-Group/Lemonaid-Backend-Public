import logging
from typing import List
import logging
from src.shared.Embedding_utils import get_embedding_gemini
from src.shared.DB_utils import retrieve_similar_content
from src.core.config import genai_client
import math



# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_context_and_ifi(data: str, top_n: int = 3) -> List[tuple[str, str]]:
    """
    For each fastener, retrieve IFI(md) and Content (string) by applying sliding window cosine similarity on vector DB

    Args:
        data (str): The data to search for
        top_n (int): The number of top matches to return
    Returns:
        List[tuple[str, str]]: A list of tuples containing the content and IFI_file_name

    Notes:
    Sliding Window Cross-Similarity:
    To handle MiniLM's token limit, input text is split into overlapping windows of 256 tokens (200 new + 56 overlapping from the previous window). 
    For each window, compute cross-similarity and select the top 3 matches. Then, across all windows, aggregate scores for duplicate rows and rank the overall top 3.
    """
    try:
        if data.strip() == "":
            return []
        
        # 1. Split the input into overlapping windows of 256 tokens
        windows = split_into_windows(data, window_size=256, stride=200)

        # 2. For each window, compute cross-similarity and select the top 3 matches
        similar_docs = dict() # key: IFI_file_name, value: score list
        file_content_map = dict() # key: IFI_file_name, value: content

        sql = """
            SELECT content, IFI_file_name, 1 - (embedding <=> %s::vector) as similarity
            FROM documents
            ORDER BY similarity DESC
            LIMIT %s
        """
        for window in windows:
            embedding_window = get_embedding_gemini(window)
            window_similar = retrieve_similar_content(sql, (embedding_window, top_n))
            for content, IFI_file_name, similarity in window_similar:
                similar_docs[IFI_file_name] = similar_docs.get(IFI_file_name, 0) + similarity
                file_content_map[IFI_file_name] = content
        
        # 3. Rank the overall top 3
        similar_docs = sorted(similar_docs.items(), key=lambda x: x[1], reverse=True)
        similar_docs = similar_docs[:top_n]

        # 4. Return the top 3 IFI_file_name and content
        most_similar_docs = [(file_content_map[IFI_file_name], IFI_file_name) for IFI_file_name, _ in similar_docs]

        logger.debug(f"[Similarity Retriever] Similar IFI_file_name values: {', '.join(ifi_name for _, ifi_name in most_similar_docs)}")
        logger.debug(f"[Similarity Retriever] Similar content values: {', '.join(content[0:100] for content, _ in most_similar_docs)}")
        return most_similar_docs
        
    except Exception as e:
        logger.error(f"[Similarity Retriever] Error: {e}")
        raise RuntimeError(f"[Similarity Retriever] Error: {e}")

def split_into_windows(data: str, window_size: int = 256, stride: int = 200) -> List[str]:
    """
    Splits text into overlapping windows using a character-to-token heuristic.
    This method avoids `compute_tokens` and works with a simple API key.

    It estimates character counts, slices the string, and then uses count_tokens
    to verify and adjust. This is much more efficient than word-by-word counting.

    Args:
        data (str): The text to be split into windows.
        window_size (int): The target size of each window in tokens.
        stride (int): The number of tokens to advance for each new window.

    Returns:
        List[str]: A list of text strings, where each string is a window.
    """
    # Rough estimate: 1 token ~ 4 characters. This is our heuristic.
    CHAR_PER_TOKEN = 4
    
    # First, a single API call to check if the whole text is small enough.
    if genai_client.models.count_tokens(model="gemini-embedding-001", contents=data).total_tokens <= window_size:
        logger.debug(f"[Window Split] The number of API calls is 1")
        return [data]
        
    windows = []
    start_char = 0
    cnt_api_calls = 0
    while start_char < len(data):
        # 1. Estimate the end character position for the window using our heuristic.
        # Ensure the estimate does not exceed the string's length.
        end_char_est = min(start_char + window_size * CHAR_PER_TOKEN, len(data))
        
        # 2. Take a substring slice based on the estimate.
        chunk = data[start_char:end_char_est]
        
        # 3. Verify the token count of our estimated chunk in a single API call.
        token_count = genai_client.models.count_tokens(model="gemini-embedding-001", contents=chunk).total_tokens
        cnt_api_calls += 1
        
        # 4. Adjust the chunk size if we are over the limit.
        # This loop will run very few times, making it efficient.
        while token_count > window_size:
            # Calculate how many characters to remove based on the token overage.
            # We remove slightly more than the bare minimum estimate to converge faster.
            overage = token_count - window_size
            chars_to_remove = math.ceil(overage * CHAR_PER_TOKEN * 0.8) # Heuristic adjustment
            
            # Prevent removing more characters than exist in the chunk
            if chars_to_remove >= len(chunk):
                chunk = ""
                break
            cnt_api_calls += 1
            chunk = chunk[:-chars_to_remove]
            token_count = genai_client.models.count_tokens(model="gemini-embedding-001", contents=chunk).total_tokens

        logger.debug(f"[Window Split] The number of API calls is {cnt_api_calls}")
        # If the chunk is empty after adjustments, stop to prevent infinite loops.
        if not chunk:
            break

        windows.append(chunk)

        # 5. Move the start position forward for the next window based on the stride heuristic.
        start_char += stride * CHAR_PER_TOKEN
            
    return windows