from typing_extensions import TypedDict
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

class MessageContent(BaseModel):
    type: str = Field(default="text", description="Type of the message content, e.g., 'text', 'image'")
    text: str = Field(description="Text content of the message")
    tokensUsed: int = Field(default=0, description="Number of tokens used in this message content")

class Message(BaseModel):
    role: str = Field(description="Role of the message sender, e.g., 'user', 'assistant'")
    content: List[MessageContent] = Field(description="List of message content objects for this message")

class ChatHistoryViewModel(TypedDict):
    id: str
    client_id: str
    product_id: str
    messages: List[Message]
    createdAt: datetime
    updatedAt: datetime