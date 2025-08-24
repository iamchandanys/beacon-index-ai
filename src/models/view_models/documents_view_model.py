import uuid

from datetime import datetime, timezone
from pydantic import BaseModel, Field

class CustomDocument(BaseModel):
    id: str | None = None
    metadata: dict = Field(default_factory=dict)
    page_content: str
    type: str = "Document"

class DocumentsViewModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    product_id: str
    chunked_documents: list[CustomDocument] = Field(default_factory=list[CustomDocument])
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    modified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())