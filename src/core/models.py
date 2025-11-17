from pydantic import BaseModel, Field
from typing import List, Optional


# models for auth


# models for chatbot
class EmailContent(BaseModel):
  to: List[str]
  cc: List[str] = []
  bcc: List[str] = []
  subject: str
  body: str


class ChatResult(BaseModel):
  text: str
  email: Optional[EmailContent] = None


class History(BaseModel):
  query: str
  file_description: str
  resources: List[str]  # List of IFI file names
  result: ChatResult


class ChatbotReq(BaseModel):
  background: Optional[str] = None
  query: str
  histories: List[History] = []


class ChatbotResult(BaseModel):
  text: str
  email: Optional[EmailContent] = None


class ChatbotRes(BaseModel):
  query: str
  file_description: str
  resources: List[str]
  result: ChatbotResult


# models for summarize
class Record(BaseModel):
  query: str
  result: str


class RecordsRequest(BaseModel):
  records: List[Record]


class ConversationCreateRequest(BaseModel):
  title: Optional[str] = Field(
    None,
    description="Title or summary of the conversation",
    examples=["RFQ Email for HEX nuts"],
    min_length=0,
    max_length=50,
  )


class ConversationResponse(BaseModel):
  conversation_id: str = Field(
    description="Unique identifier for the conversation",
    examples=["219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01"],
  )
  title: Optional[str] = Field(
    None,
    description="Title or summary of the conversation",
    examples=["RFQ Email for HEX nuts"],
  )
  created_at: str = Field(
    description="Timestamp when the conversation was created",
    examples=["2025-10-10T14:30:00Z"],
  )
  updated_at: str = Field(
    description="Timestamp when the conversation was last updated",
    examples=["2025-10-10T15:45:00Z"],
  )


class ConversationsResponse(BaseModel):
  conversations: List[ConversationResponse] = Field(
    description="List of conversation objects"
  )
  count: int = Field(
    description="Total number of conversations returned", examples=[10]
  )


class AttachmentCreateRequest(BaseModel):
  s3_url: str = Field(
    description="S3 URL of the attachment",
    examples=["https://s3.amazonaws.com/bucket/file.pdf"],
  )
  filename: str = Field(
    description="Display filename for the attachment", examples=["product_specs.pdf"]
  )
  file_type: str = Field(
    description="MIME type of the file", examples=["application/pdf"]
  )


class AttachmentResponse(BaseModel):
  attachment_id: str = Field(
    description="Unique identifier for the attachment",
    examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
  )
  s3_url: str = Field(
    description="S3 URL of the attachment",
    examples=["https://s3.amazonaws.com/bucket/file.pdf"],
  )
  filename: str = Field(
    description="Display filename for the attachment", examples=["product_specs.pdf"]
  )
  file_type: str = Field(
    description="MIME type of the file", examples=["application/pdf"]
  )
  created_at: str = Field(
    description="Timestamp when the attachment was created",
    examples=["2025-10-10T14:30:00Z"],
  )


class MessageCreateRequest(BaseModel):
  query: Optional[str] = Field(
    None,
    description="User entered query",
    examples=["Create RFQ email for the attached files"],
  )
  file_description: Optional[str] = Field(
    None,
    description="Information retrieved from the attached files.",
    examples=["Product: M8 HEX nuts, Quantity: 1000 units, Material: Stainless Steel"],
  )
  resources: List[str] = Field(
    [],
    description="Relevant documents retrieved using cosine similarity.",
    examples=[["doc_id_123", "doc_id_456"]],
  )
  result_text: str = Field(
    description="Gemini responses for user query",
    examples=["Please find the RFQ email for the fasteners below."],
  )
  email: Optional[str] = Field(
    None,
    description="JSON string for email",
    examples=['{"subject": "RFQ for HEX nuts", "body": "Dear Supplier..."}'],
  )
  attachments: Optional[List[AttachmentCreateRequest]] = Field(
    None,
    description="List of attachments for this message",
    examples=[
      [
        {
          "s3_url": "https://s3.amazonaws.com/bucket/file.pdf",
          "filename": "specs.pdf",
          "file_type": "application/pdf",
        }
      ]
    ],
  )


class MessageResponse(BaseModel):
  message_id: str = Field(
    description="Unique identifier for the message",
    examples=["87af8ec5-83a4-4794-834c-d5533acee7bc"],
  )
  conversation_id: str = Field(
    description="ID of the conversation this message belongs to",
    examples=["219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01"],
  )
  query: Optional[str] = Field(
    None,
    description="User's original query",
    examples=["Create RFQ email for the attached files"],
  )
  file_description: Optional[str] = Field(
    None,
    description="Information extracted from attached files",
    examples=["Product: M8 HEX nuts, Quantity: 1000 units"],
  )
  resources: List[str] = Field(
    [],
    description="List of relevant document IDs",
    examples=[["doc_id_123", "doc_id_456"]],
  )
  result_text: str = Field(
    description="Generated response text from Gemini",
    examples=["Please find the RFQ email for the fasteners below."],
  )
  email: Optional[str] = Field(
    None,
    description="Generated email content as JSON string",
    examples=['{"subject": "RFQ for HEX nuts", "body": "Dear Supplier..."}'],
  )
  attachments: List[AttachmentResponse] = Field(
    default=[],
    description="List of attachments for this message",
    examples=[
      [
        {
          "attachment_id": "att-123",
          "s3_url": "https://...",
          "filename": "file.pdf",
          "file_type": "application/pdf",
          "created_at": "2025-10-10T14:30:00Z",
        }
      ]
    ],
  )
  created_at: str = Field(
    description="Timestamp when the message was created",
    examples=["2025-10-10T14:30:00Z"],
  )
  updated_at: str = Field(
    description="Timestamp when the message was last updated",
    examples=["2025-10-10T14:30:00Z"],
  )


class MessagesCreateRequest(BaseModel):
  messages: List[MessageCreateRequest] = Field(description="List of message objects")
  count: int = Field(description="Total number of messages to be created")


class MessagesResponse(BaseModel):
  messages: List[MessageResponse] = Field(description="List of message objects")
  count: int = Field(description="Total number of messages returned", examples=[5])

class Files(BaseModel):
  filename: str = Field(description="Filename of the file", examples=["file.pdf"])
  file_type: str = Field(description="File type of the file", examples=["application/pdf"])
  file_size: Optional[int] = Field(None, description="File size of the file", examples=[1000]) # optional

class UploadFilesInfo(BaseModel):
  filename: str = Field(description="Filename of the file", examples=["file.pdf"])
  upload_url: str = Field(description="Upload URL of the file", examples=["https://s3.amazonaws.com/bucket/file.pdf"])
  s3_key: str = Field(description="S3 key of the file", examples=["attachments/user-123/conv-456/file.pdf"])

class UploadFilesRequest(BaseModel):
  files: List[Files] = Field(description="List of files to be uploaded", examples=[[{"filename": "file.pdf", "file_type": "application/pdf", "file_size": 1000}]])

class UploadFilesResponse(BaseModel):
  files: List[UploadFilesInfo] = Field(description="List of uploaded files", examples=[["file.pdf", "https://s3.amazonaws.com/bucket/file.pdf", "attachments/user-123/conv-456/file.pdf"]])