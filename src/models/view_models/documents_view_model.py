import uuid

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain.schema import Document

class DocumentsViewModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    product_id: str
    chunked_documents: list[Document] = Field(default_factory=list[Document])
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    modified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())