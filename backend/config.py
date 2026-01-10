"""
配置管理模块
Configuration Management Module
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ 已加载配置文件: {env_path}")
else:
    print("⚠️  未找到 .env 文件，使用默认配置")

# ============================================
# 数据存储配置
# ============================================
KNOWLEDGE_DB_PATH = os.getenv('KNOWLEDGE_DB_PATH', './knowledge_db')
INSPIRATION_DB_PATH = os.getenv('INSPIRATION_DB_PATH', './inspiration_db')
BACKUP_DB_PATH = os.getenv('BACKUP_DB_PATH', './backup.db')
TODO_DB_PATH = os.getenv('TODO_DB_PATH', './backup.db') # Default to same backup db

# ============================================
# 向量模型配置
# ============================================
EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'BAAI/bge-small-zh-v1.5')
EMBEDDING_MODEL_PATH = os.getenv('EMBEDDING_MODEL_PATH', None)

# ============================================
# AI 模型配置
# ============================================
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'Qwen/Qwen2.5-1.5B-Instruct')
AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', None)
DISABLE_AI_MODEL = os.getenv('DISABLE_AI_MODEL', 'false').lower() == 'true'

# ============================================
# HuggingFace 配置
# ============================================
# 本地文件优先模式（推荐使用，不会完全禁止联网）
LOCAL_FILES_ONLY = os.getenv('LOCAL_FILES_ONLY', 'true').lower() == 'true'

# 完全离线模式（非常严格，可能导致加载失败）
# 注意：transformers 在完全离线模式下即使模型已缓存也可能无法加载
# 推荐使用 LOCAL_FILES_ONLY 而不是 HF_HUB_OFFLINE
HF_HUB_OFFLINE_STRICT = os.getenv('HF_HUB_OFFLINE', 'false').lower() == 'true'

# 设置环境变量
if HF_HUB_OFFLINE_STRICT:
    print("⚠️  警告：HF_HUB_OFFLINE=true 会导致 transformers 无法加载已缓存的模型")
    print("   即使模型已完整缓存，transformers 也需要访问元数据")
    print("   正在强制禁用 HF_HUB_OFFLINE 以允许加载本地缓存的模型...")
    # 强制取消设置这些严格的离线变量
    os.environ.pop('HF_HUB_OFFLINE', None)
    os.environ.pop('TRANSFORMERS_OFFLINE', None)
    os.environ.pop('HF_DATASETS_OFFLINE', None)
    print("   ✅ 已禁用严格离线模式，现在使用 LOCAL_FILES_ONLY 替代")

# 设置 sentence-transformers 缓存目录
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path.home() / '.cache' / 'torch' / 'sentence_transformers')

if LOCAL_FILES_ONLY:
    print("✅ 本地文件优先模式（优先使用缓存，必要时可访问元数据）")
else:
    print("⚠️  在线模式（允许下载模型）")

# HuggingFace 缓存目录
HF_HOME = os.getenv('HF_HOME', None)
if HF_HOME:
    os.environ['HF_HOME'] = HF_HOME
    print(f"✅ HuggingFace 缓存目录: {HF_HOME}")

# 使用镜像
HF_ENDPOINT = os.getenv('HF_ENDPOINT', None)
if HF_ENDPOINT:
    os.environ['HF_ENDPOINT'] = HF_ENDPOINT
    print(f"✅ 使用 HuggingFace 镜像: {HF_ENDPOINT}")

# 禁用代理（避免代理错误）
os.environ['NO_PROXY'] = '*'
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''

# ============================================
# Web 服务配置
# ============================================
WEB_HOST = os.getenv('WEB_HOST', '0.0.0.0')
WEB_PORT = int(os.getenv('WEB_PORT', '8000'))

# ============================================
# 搜索配置
# ============================================
DEFAULT_SEARCH_TOP_K = int(os.getenv('DEFAULT_SEARCH_TOP_K', '5'))
VECTOR_SIMILARITY_WEIGHT = float(os.getenv('VECTOR_SIMILARITY_WEIGHT', '0.85'))
KEYWORD_MATCH_WEIGHT = float(os.getenv('KEYWORD_MATCH_WEIGHT', '0.15'))


def print_config():
    """打印当前配置"""
    print("\n" + "=" * 50)
    print("当前配置 (Current Configuration)")
    print("=" * 50)
    print(f"笔记向量库路径: {KNOWLEDGE_DB_PATH}")
    print(f"灵感向量库路径: {INSPIRATION_DB_PATH}")
    print(f"备份数据库路径: {BACKUP_DB_PATH}")
    print(f"向量模型: {EMBEDDING_MODEL_NAME}")
    if EMBEDDING_MODEL_PATH:
        print(f"向量模型路径: {EMBEDDING_MODEL_PATH}")
    print(f"AI 模型: {AI_MODEL_NAME if not DISABLE_AI_MODEL else '已禁用'}")
    if AI_MODEL_PATH:
        print(f"AI 模型路径: {AI_MODEL_PATH}")
    print(f"本地文件优先: {'是' if LOCAL_FILES_ONLY else '否'}")
    if HF_HUB_OFFLINE_STRICT:
        print(f"⚠️  完全离线模式: 是（不推荐，可能导致加载失败）")
    print(f"Web 服务: {WEB_HOST}:{WEB_PORT}")
    print("=" * 50 + "\n")

