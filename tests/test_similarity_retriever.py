# tests/test_similarity_retriever.py
import pytest
from unittest.mock import Mock, patch
from src.lib.similarity_retriever import get_context_and_ifi, split_into_windows

@pytest.fixture(autouse=True)
def mock_tokenizer():
    """Mock tokenizer for testing window splitting"""
    with patch('src.lib.similarity_retriever.tokenizer') as mock_tok:
        def mock_encode(text):
            # For test input like "window1 " * 100, make each "windowN " be exactly 100 tokens
            # This way we can precisely control window sizes
            tokens = []
            if "window1" in text:
                tokens.extend(range(200))  # First 200 tokens
            if "window2" in text:
                tokens.extend(range(200, 400))  # Next 200 tokens
            if "window3" in text:
                tokens.extend(range(400, 600))  # Next 200 tokens
            return tokens if tokens else list(range(len(text.split())))
            
        mock_tok.encode.side_effect = mock_encode
        yield mock_tok

@pytest.fixture
def mock_dependencies():
    """Mock get_embedding and retrieve_similar_content functions"""
    with patch('src.lib.similarity_retriever.get_embedding') as mock_get_embedding, \
         patch('src.lib.similarity_retriever.retrieve_similar_content') as mock_retrieve:
        
        def mock_embedding_fn(tokens):
            # Return different embeddings based on content
            if isinstance(tokens, list):  # Handle tokenized input
                text = ' '.join(map(str, tokens))
            else:
                text = tokens
                
            if any(str(x) < "200" for x in tokens):  # window1 tokens
                return [0.1, 0.2, 0.3]
            elif any("200" <= str(x) < "400" for x in tokens):  # window2 tokens
                return [0.4, 0.5, 0.6]
            return [0.7, 0.8, 0.9]  # window3 tokens
        
        mock_get_embedding.side_effect = mock_embedding_fn

        def mock_retrieve_fn(sql, params):
            embedding = params[0]
            # Return consistent results for specific windows
            if embedding == [0.1, 0.2, 0.3]:  # window1
                return [
                    ("content2", "IFI_2", 0.95),  # IFI_2 appears with highest score
                    ("content1", "IFI_1", 0.85),
                    ("content3", "IFI_3", 0.75)
                ]
            elif embedding == [0.4, 0.5, 0.6]:  # window2
                return [
                    ("content2", "IFI_2", 0.92),  # IFI_2 appears again with high score
                    ("content4", "IFI_4", 0.82),
                    ("content1", "IFI_1", 0.72)
                ]
            else:  # window3
                return [
                    ("content2", "IFI_2", 0.88),  # IFI_2 appears third time
                    ("content5", "IFI_5", 0.85),
                    ("content6", "IFI_6", 0.70)
                ]
        
        mock_retrieve.side_effect = mock_retrieve_fn
        mock_retrieve.reset_mock()
        
        yield mock_get_embedding, mock_retrieve

@pytest.mark.asyncio
async def test_get_context_and_ifi_score_accumulation(mock_dependencies):
    """Test that similarity scores are properly accumulated"""
    mock_get_embedding, mock_retrieve = mock_dependencies
    
    # This will create exactly 200 tokens
    input_text = "window1 " * 100
    
    results = await get_context_and_ifi(input_text, top_n=4)
    
    # Get IFI names from results
    result_ifis = [ifi for _, ifi in results]
    
    # Verify IFI_2 is present and ranked first (highest accumulated score)
    assert "IFI_2" in result_ifis, "IFI_2 should be present (highest accumulated score)"
    assert result_ifis.index("IFI_2") == 0, "IFI_2 should be ranked first"
    
    # Verify number of retrieve calls
    assert mock_retrieve.call_count == 1, "Should make exactly one retrieve call for one window"

@pytest.mark.asyncio
async def test_get_context_and_ifi_window_coverage(mock_dependencies):
    """Test that results come from multiple windows"""
    mock_get_embedding, mock_retrieve = mock_dependencies
    
    # This will create exactly 600 tokens (3 windows of 200 tokens each)
    input_text = "window1 " * 100 + "window2 " * 100 + "window3 " * 100
    
    results = await get_context_and_ifi(input_text, top_n=5)
    
    # Verify number of retrieve calls matches number of windows
    assert mock_retrieve.call_count == 3, "Should make exactly three retrieve calls"
    
    # Verify results include documents from different windows
    result_ifis = [ifi for _, ifi in results]
    assert "IFI_2" in result_ifis, "Should include document appearing in multiple windows"
    assert result_ifis.index("IFI_2") == 0, "IFI_2 should be ranked first (highest total score)"
    
@pytest.mark.asyncio
async def test_get_context_and_ifi_duplicate_files(mock_dependencies):
    """Test handling of documents that appear multiple times with different scores"""
    mock_get_embedding, mock_retrieve = mock_dependencies
    
    # Create input that will generate multiple windows
    input_text = "window1 " * 100 + "window2 " * 100 + "window3 " * 100
    
    results = await get_context_and_ifi(input_text, top_n=3)
    
    # IFI_2 should be first because it appears in all windows with high scores
    # Total score for IFI_2 = 0.95 + 0.92 + 0.88 = 2.75
    result_ifis = [ifi for _, ifi in results]
    assert result_ifis[0] == "IFI_2", "IFI_2 should be ranked first (appears in all windows with high scores)"