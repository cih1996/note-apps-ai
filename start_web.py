"""
启动 Web 服务器
Start Web Server
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 先加载配置
from backend.config import WEB_HOST, WEB_PORT, print_config

# 打印配置
print_config()

from backend.api import app
import uvicorn

if __name__ == "__main__":
    print("🚀 启动向量知识库 Web 服务...")
    print(f"📍 访问地址: http://localhost:{WEB_PORT}")
    print(f"📖 API 文档: http://localhost:{WEB_PORT}/docs")
    print("⏹️  按 Ctrl+C 停止服务\n")
    
    uvicorn.run(
        app,
        host=WEB_HOST,
        port=WEB_PORT,
        reload=False  # 生产环境关闭自动重载
    )

