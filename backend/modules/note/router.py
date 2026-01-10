from fastapi import APIRouter, HTTPException
from typing import List, Optional
from .models import NoteCreate, NoteUpdate, SearchQuery, NoteResponse
from .service import NoteService

router = APIRouter(prefix="/api/note", tags=["note"])
note_service = NoteService()

@router.post("/add")
async def add_note(note: NoteCreate):
    if not note.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    return note_service.add_note(note.content, note.description, note.tags)

@router.post("/search")
async def search_notes(search: SearchQuery):
    return note_service.search_notes(search.query, top_k=search.top_k, filter_tags=search.tags)

@router.get("/list")
async def get_all_notes():
    return note_service.get_all_notes()

@router.get("/tags")
async def get_all_tags():
    return note_service.get_all_tags()

@router.get("/get/{note_id}")
async def get_note(note_id: str):
    note = note_service.get_note_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note

@router.put("/update/{note_id}")
async def update_note(note_id: str, note: NoteCreate):
    if not note.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    success = note_service.update_note(note_id, note.content, note.description, note.tags)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在或更新失败")
    return {"status": "success", "id": note_id}

@router.delete("/delete/{note_id}")
async def delete_note(note_id: str):
    success = note_service.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"status": "success"}

