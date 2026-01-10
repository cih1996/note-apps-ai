from pydantic import BaseModel
from typing import Optional, List

class InspirationCreate(BaseModel):
    content: str  # Original raw content

class InspirationUpdate(BaseModel):
    content: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5

class InspirationResponse(BaseModel):
    id: str
    content: str
    title: str
    theme: str
    summary: str
    tags: List[str]
    created_at: str
    updated_at: Optional[str] = None
    similarity: Optional[float] = None

