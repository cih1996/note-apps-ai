from fastapi import APIRouter, HTTPException
from typing import List
from .models import TodoCreate, TodoAIParseRequest, TodoUpdateStatus, SubTaskUpdate, TodoUpdateInfo
from .service import TodoService

router = APIRouter(prefix="/api/todo", tags=["todo"])
todo_service = TodoService()

@router.post("/parse")
async def parse_todo(request: TodoAIParseRequest):
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    return todo_service.parse_with_ai(request.content)

@router.post("/add")
async def add_todos(request: TodoCreate):
    if not request.items:
        raise HTTPException(status_code=400, detail="任务列表不能为空")
    success = todo_service.add_todos([item.model_dump() for item in request.items])
    return {"status": "success"}

@router.get("/list")
async def get_all_todos():
    return todo_service.get_all_todos()

@router.put("/update/{todo_id}")
async def update_todo_status(todo_id: str, request: TodoUpdateStatus):
    success = todo_service.update_status(todo_id, request.status, request.completed_at)
    return {"status": "success"}

@router.put("/update_info/{todo_id}")
async def update_todo_info(todo_id: str, request: TodoUpdateInfo):
    success = todo_service.update_info(todo_id, request.task, request.priority)
    return {"status": "success"}

@router.put("/update/{todo_id}/subtask")
async def update_subtask_status(todo_id: str, request: SubTaskUpdate):
    success = todo_service.update_subtask_status(todo_id, request.subtask_id, request.status, request.completed_at)
    if not success:
        raise HTTPException(status_code=404, detail="待办事项不存在")
    return {"status": "success"}

@router.delete("/delete/{todo_id}")
async def delete_todo(todo_id: str):
    success = todo_service.delete_todo(todo_id)
    return {"status": "success"}

