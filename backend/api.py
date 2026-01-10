from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from backend.modules.note import note_router
from backend.modules.inspiration import inspiration_router
from backend.modules.todo import todo_router

app = FastAPI(title="Vector Knowledge Base API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend-src/dist")

# 挂载静态文件目录
if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

# 注册路由模块
app.include_router(note_router)
app.include_router(inspiration_router)
app.include_router(todo_router)

@app.get("/")
async def read_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="前端页面不存在:"+FRONTEND_DIR)
    return FileResponse(index_path)

if __name__ == "__main__":
    from backend.config import WEB_HOST, WEB_PORT
    uvicorn.run(app, host=WEB_HOST, port=WEB_PORT)
