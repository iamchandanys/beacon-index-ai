from pydantic import BaseModel, Field
from typing import List, Union

class DocAnalyserMetadata(BaseModel):
    summary: List[str] = Field(default_factory=list, description="Summary of the document")
    title: str = Field(..., description="Title of the document")
    author: str = Field(..., description="Author of the document")
    date_created: str = Field(..., description="Creation date of the document")
    last_modified_date: str = Field(..., description="Last modified date of the document")
    publisher: str = Field(..., description="Publisher of the document")
    language: str = Field(..., description="Language of the document")
    page_count: Union[int, str] = Field(..., description="Page count of the document")
    sentiment_tone: str = Field(..., description="Sentiment tone of the document")