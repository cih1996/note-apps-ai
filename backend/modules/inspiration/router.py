from fastapi import APIRouter, HTTPException
from typing import List, Optional
from .models import InspirationCreate, InspirationUpdate, SearchQuery, InspirationResponse
from .service import InspirationService

router = APIRouter(prefix="/api/inspiration", tags=["inspiration"])
inspiration_service = InspirationService()

@router.post("/add")
async def add_inspiration(item: InspirationCreate):
    if not item.content.strip():
        raise HTTPException(status_code=400, detail="内容不能为空")
    return inspiration_service.add_inspiration(item.content)

@router.post("/search")
async def search_inspirations(search: SearchQuery):
    return inspiration_service.search_inspirations(search.query, top_k=search.top_k)

@router.get("/list")
async def get_all_inspirations(limit: int = 20, offset: int = 0):
    return inspiration_service.get_all_inspirations(limit=limit, offset=offset)

@router.delete("/delete/{inspiration_id}")
async def delete_inspiration(inspiration_id: str):
    success = inspiration_service.delete_inspiration(inspiration_id)
    if not success:
        raise HTTPException(status_code=404, detail="灵感不存在")
    return {"status": "success"}

