from pydantic import BaseModel
from typing import Optional, List

class SubTask(BaseModel):
    id: Optional[str] = None
    task: str
    status: str = "pending"
    completed_at: Optional[str] = None

class TodoItem(BaseModel):
    id: Optional[str] = None
    task: str
    priority: str  # 紧急, 近期, 长期, 待定
    status: str = "pending" # pending, completed
    subtasks: Optional[List[SubTask]] = []
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    reminder_at: Optional[str] = None

class TodoCreate(BaseModel):
    items: List[TodoItem]

class TodoAIParseRequest(BaseModel):
    content: str

class TodoUpdateStatus(BaseModel):
    status: str
    completed_at: Optional[str] = None

class TodoUpdateInfo(BaseModel):
    task: str
    priority: str

class SubTaskUpdate(BaseModel):
    subtask_id: str
    status: str
    completed_at: Optional[str] = None

