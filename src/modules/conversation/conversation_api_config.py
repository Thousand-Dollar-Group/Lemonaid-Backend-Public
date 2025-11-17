from fastapi import status

# Conversation endpoints configuration
CREATE_CONVERSATION_CONFIG = {
  "summary": "Create a new conversation",
  "description": "Creates a new conversation for the authenticated user with an optional title.",
  "status_code": status.HTTP_201_CREATED,
  "responses": {
    201: {
      "description": "Conversation created successfully",
      "content": {
        "application/json": {
          "example": {
            "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
            "title": "RFQ Email for HEX nuts",
            "created_at": "2025-10-10T12:00:00Z",
            "updated_at": "2025-10-10T12:00:00Z",
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    422: {
      "description": "Validation Error - Invalid request body",
      "content": {
        "application/json": {
          "example": {
            "detail": [
              {
                "loc": ["body", "title"],
                "msg": "field required",
                "type": "value_error.missing",
              }
            ]
          }
        }
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}

READ_CONVERSATIONS_CONFIG = {
  "summary": "Get all conversations",
  "description": "Retrieves all conversations belonging to the authenticated user.",
  "status_code": status.HTTP_200_OK,
  "responses": {
    200: {
      "description": "Conversations retrieved successfully",
      "content": {
        "application/json": {
          "example": {
            "conversations": [
              {
                "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
                "title": "My First Conversation",
                "created_at": "2025-10-10T12:00:00Z",
                "updated_at": "2025-10-10T12:00:00Z",
              },
              {
                "conversation_id": "bbca4472-3cc3-4bf4-8c31-e28bf4fd17a9",
                "title": "My Second Conversation",
                "created_at": "2025-10-09T14:30:00Z",
                "updated_at": "2025-10-09T14:30:00Z",
              },
            ],
            "total": 2,
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}

# Message endpoints configuration
CREATE_MESSAGE_CONFIG = {
  "summary": "Create a new message",
  "description": "Creates a new message within a specific conversation. Supports adding queries, file descriptions, resources, result text, email information, and attachments.",
  "status_code": status.HTTP_201_CREATED,
  "responses": {
    201: {
      "description": "Message created successfully",
      "content": {
        "application/json": {
          "example": {
            "message_id": "87af8ec5-83a4-4794-834c-d5533acee7bc",
            "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
            "query": "Create RFQ email for the attached files",
            "file_description": "Product: M8 HEX nuts, Quantity: 1000 units",
            "resources": ["doc_id_123", "doc_id_456"],
            "result_text": "Please find the RFQ email for the fasteners below.",
            "email": '{"subject": "RFQ for HEX nuts", "body": "Dear Supplier..."}',
            "attachments": [
              {
                "attachment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "s3_url": "https://s3.amazonaws.com/bucket/specs.pdf",
                "filename": "product_specs.pdf",
                "file_type": "application/pdf",
                "created_at": "2025-10-10T12:05:00Z",
              },
              {
                "attachment_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "s3_url": "https://s3.amazonaws.com/bucket/drawing.pdf",
                "filename": "technical_drawing.pdf",
                "file_type": "application/pdf",
                "created_at": "2025-10-10T12:05:00Z",
              },
            ],
            "created_at": "2025-10-10T12:05:00Z",
            "updated_at": "2025-10-10T12:05:00Z",
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    403: {
      "description": "Forbidden - User does not have access to this conversation",
      "content": {
        "application/json": {
          "example": {
            "detail": "You do not have permission to access this conversation"
          }
        }
      },
    },
    404: {
      "description": "Not Found - Conversation does not exist",
      "content": {
        "application/json": {"example": {"detail": "Conversation not found"}}
      },
    },
    422: {
      "description": "Validation Error - Invalid request body",
      "content": {
        "application/json": {
          "example": {
            "detail": [
              {
                "loc": ["body", "query"],
                "msg": "field required",
                "type": "value_error.missing",
              }
            ]
          }
        }
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}

CREATE_MESSAGES_CONFIG = {
  "summary": "Create multiple messages",
  "description": "Creates multiple messages within a specific conversation in a single request. Supports batch creation of messages with queries, file descriptions, resources, result text, email information, and attachments.",
  "status_code": status.HTTP_201_CREATED,
  "responses": {
    201: {
      "description": "Messages created successfully",
      "content": {
        "application/json": {
          "example": {
            "messages": [
              {
                "message_id": "87af8ec5-83a4-4794-834c-d5533acee7bc",
                "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
                "query": "Create RFQ email for the attached files",
                "file_description": "Product: M8 HEX nuts, Quantity: 1000 units",
                "resources": ["doc_id_123", "doc_id_456"],
                "result_text": "Please find the RFQ email for the fasteners below.",
                "email": '{"subject": "RFQ for HEX nuts", "body": "Dear Supplier..."}',
                "attachments": [
                  {
                    "attachment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "s3_url": "https://s3.amazonaws.com/bucket/specs.pdf",
                    "filename": "product_specs.pdf",
                    "file_type": "application/pdf",
                    "created_at": "2025-10-10T12:05:00Z",
                  }
                ],
                "created_at": "2025-10-10T12:05:00Z",
                "updated_at": "2025-10-10T12:05:00Z",
              },
              {
                "message_id": "92bf9fd6-94b5-5805-945d-e6644bdeffc2",
                "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
                "query": "Follow up on previous RFQ",
                "file_description": None,
                "resources": ["doc_id_789"],
                "result_text": "The follow-up email has been prepared.",
                "email": '{"subject": "Re: RFQ for HEX nuts", "body": "Following up..."}',
                "attachments": [],
                "created_at": "2025-10-10T12:06:00Z",
                "updated_at": "2025-10-10T12:06:00Z",
              },
            ],
            "count": 2,
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    403: {
      "description": "Forbidden - User does not have access to this conversation",
      "content": {
        "application/json": {
          "example": {
            "detail": "You do not have permission to access this conversation"
          }
        }
      },
    },
    404: {
      "description": "Not Found - Conversation does not exist",
      "content": {
        "application/json": {"example": {"detail": "Conversation not found"}}
      },
    },
    422: {
      "description": "Validation Error - Invalid request body",
      "content": {
        "application/json": {
          "example": {
            "detail": [
              {
                "loc": ["body", "messages", 0, "result_text"],
                "msg": "field required",
                "type": "value_error.missing",
              }
            ]
          }
        }
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}

READ_MESSAGES_CONFIG = {
  "summary": "Get all messages in a conversation",
  "description": "Retrieves all messages within a specific conversation for the authenticated user, including their attachments.",
  "status_code": status.HTTP_200_OK,
  "responses": {
    200: {
      "description": "Messages retrieved successfully",
      "content": {
        "application/json": {
          "example": {
            "messages": [
              {
                "message_id": "87af8ec5-83a4-4794-834c-d5533acee7bc",
                "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
                "query": "Create RFQ email for the attached files",
                "file_description": "Product: M8 HEX nuts, Quantity: 1000 units",
                "resources": ["doc_id_123", "doc_id_456"],
                "result_text": "Please find the RFQ email for the fasteners below.",
                "email": '{"subject": "RFQ for HEX nuts", "body": "Dear Supplier..."}',
                "attachments": [
                  {
                    "attachment_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "s3_url": "https://s3.amazonaws.com/bucket/specs.pdf",
                    "filename": "product_specs.pdf",
                    "file_type": "application/pdf",
                    "created_at": "2025-10-10T12:05:00Z",
                  },
                  {
                    "attachment_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                    "s3_url": "https://s3.amazonaws.com/bucket/drawing.pdf",
                    "filename": "technical_drawing.pdf",
                    "file_type": "application/pdf",
                    "created_at": "2025-10-10T12:05:00Z",
                  },
                ],
                "created_at": "2025-10-10T12:05:00Z",
                "updated_at": "2025-10-10T12:05:00Z",
              },
              {
                "message_id": "cf85c6db-cbda-4f1e-bf6d-d2215f199579",
                "conversation_id": "219ba1b4-2d7c-47a5-a4b0-ad6d40d0bf01",
                "query": "Do you speak other languages?",
                "file_description": None,
                "resources": [],
                "result_text": "Yes, I do. Which language would you prefer?",
                "email": None,
                "attachments": [],
                "created_at": "2025-10-10T12:10:00Z",
                "updated_at": "2025-10-10T12:10:00Z",
              },
            ],
            "total": 2,
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    403: {
      "description": "Forbidden - User does not have access to this conversation",
      "content": {
        "application/json": {
          "example": {
            "detail": "You do not have permission to access this conversation"
          }
        }
      },
    },
    404: {
      "description": "Not Found - Conversation does not exist",
      "content": {
        "application/json": {"example": {"detail": "Conversation not found"}}
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}

UPLOAD_FILES_CONFIG = {
  "summary": "Upload attachments URLs",
  "description": "Uploads attachments URLs for a specific conversation.",
  "status_code": status.HTTP_200_OK,
  "responses": {
    200: {
      "description": "Attachments URLs uploaded successfully",
      "content": {
        "application/json": {
          "example": {
            "files": [
              {
                "filename": "report.pdf",
                "file_type": "application/pdf",
                "file_size": 1024000
              },
              {
                "filename": "chart.jpg",
                "file_type": "image/jpeg",
                "file_size": 524288
              }
            ],
          }
        }
      },
    },
    401: {
      "description": "Unauthorized - Invalid or missing access token",
      "content": {
        "application/json": {
          "example": {"detail": "Invalid authentication credentials"}
        }
      },
    },
    403: {
      "description": "Forbidden - User does not have access to this conversation",
      "content": {
        "application/json": {
          "example": {
            "detail": "You do not have permission to access this conversation"
          }
        }
      },
    },
    404: {
      "description": "Not Found - Conversation does not exist",
      "content": {
        "application/json": {"example": {"detail": "Conversation not found"}}
      },
    },
    500: {
      "description": "Internal Server Error",
      "content": {
        "application/json": {"example": {"detail": "An unexpected error occurred"}}
      },
    },
  },
  "tags": ["Conversation"],
}