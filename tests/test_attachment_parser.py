# test_attachment_parser.py
import pytest
from fastapi import UploadFile
import os
from unittest.mock import Mock, patch

# First import google.genai normally
import google.genai

# Set environment variables before importing our module
os.environ['GEMINI_API_KEY'] = 'fake-api-key'
os.environ['GEMINI_MODEL'] = 'fake-model'

# Now import our module
from src.lib.attachment_parser import attachment_parser, attachments_parser

# Test data directory
TEST_DATA_DIR = "test_data"

@pytest.fixture(autouse=True)
def mock_genai_client():
    """Mock all Gemini client operations"""
    with patch('google.genai.Client', autospec=True) as mock_client_class:
        # Create mock client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock file operations
        mock_file = Mock()
        mock_file.name = "mock_gemini_file"
        mock_client.files.upload = Mock(return_value=mock_file)
        mock_client.files.get = Mock(return_value=mock_file)
        
        # Mock content generation
        mock_response = Mock()
        mock_response.text = "Generated description"
        mock_client.models.generate_content = Mock(return_value=mock_response)
        
        yield mock_client

@pytest.fixture
def setup_test_env():
    """Setup test environment"""
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    yield
    # Cleanup after tests
    for file in os.listdir(TEST_DATA_DIR):
        os.remove(os.path.join(TEST_DATA_DIR, file))
    os.rmdir(TEST_DATA_DIR)

@pytest.fixture
def mock_excel_file():
    """Create a mock Excel file upload"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.xlsx"
    mock_file.content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    mock_file.file = Mock()
    mock_file.file.read.return_value = b"mock excel content"
    return mock_file

@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file upload"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.file = Mock()
    mock_file.file.read.return_value = b"mock pdf content"
    return mock_file

@pytest.mark.asyncio
async def test_attachment_parser_excel(setup_test_env, mock_excel_file, mock_genai_client):
    """Test parsing Excel file"""
    with patch('pandas.read_excel') as mock_read_excel:
        mock_df = Mock()
        mock_df.to_json.return_value = '{"data": "test"}'
        mock_read_excel.return_value = mock_df
        
        content, file_type = await attachment_parser(mock_excel_file, TEST_DATA_DIR)
        
        assert file_type == "sheet"
        assert content.startswith("Sheet Content: ")
        assert "test" in content

@pytest.mark.asyncio
async def test_attachment_parser_pdf(setup_test_env, mock_pdf_file, mock_genai_client):
    """Test parsing PDF file"""
    content, file_type = await attachment_parser(mock_pdf_file, TEST_DATA_DIR)
    
    assert file_type == "file"
    assert content == "mock_gemini_file"
    mock_genai_client.files.upload.assert_called_once()

@pytest.mark.asyncio
async def test_attachment_parser_unsupported_file(setup_test_env, mock_genai_client):
    """Test parsing unsupported file type"""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    
    content, file_type = await attachment_parser(mock_file, TEST_DATA_DIR)
    
    assert content is None
    assert file_type is None
    mock_genai_client.files.upload.assert_not_called()

@pytest.mark.asyncio
async def test_attachments_parser_multiple_files(setup_test_env, mock_excel_file, mock_pdf_file, mock_genai_client):
    """Test parsing multiple attachments"""
    with patch('pandas.read_excel') as mock_read_excel:
        mock_df = Mock()
        mock_df.to_json.return_value = '{"data": "test"}'
        mock_read_excel.return_value = mock_df
        
        description = await attachments_parser(
            attachments=[mock_excel_file, mock_pdf_file],
            file_dir=TEST_DATA_DIR
        )
        
        assert description == "Generated description"
        assert mock_genai_client.models.generate_content.called
