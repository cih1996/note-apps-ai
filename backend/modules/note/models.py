from pydantic import BaseModel
from typing import Optional, List

class NoteCreate(BaseModel):
    content: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5
    tags: Optional[List[str]] = None

class NoteResponse(BaseModel):
    id: str
    content: str
    user_description: str
    ai_description: str
    tags: List[str] = []
    created_at: str
    updated_at: Optional[str] = None
    similarity: Optional[float] = None

