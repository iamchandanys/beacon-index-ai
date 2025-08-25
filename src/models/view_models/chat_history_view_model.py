import uuid

from pydantic import BaseModel, Field
from datetime import datetime, timezone

class MessageContent(BaseModel):
    type: str = Field(default="text", description="Type of the message content, e.g., 'text', 'image'")
    text: str = Field(description="Text content of the message")
    tokensUsed: int = Field(default=0, description="Number of tokens used in this message content")

class Message(BaseModel):
    role: str = Field(description="Role of the message sender, e.g., 'user', 'assistant'")
    content: list[MessageContent] = Field(description="List of message content objects for this message")

class ChatHistoryViewModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the chat history")
    client_id: str = Field(description="Client identifier")
    product_id: str = Field(description="Product identifier")
    messages: list[Message] = Field(default_factory=list[Message], description="List of messages in the chat")
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Creation timestamp")
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="Last updated timestamp")