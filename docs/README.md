# 🧠 向量知识库笔记系统 (Vector Notes)

一个基于向量匹配的个人笔记系统，**无需分类标签**，通过语义搜索即可找到内容。

## ✨ 核心特性

- 🚫 **无需分类** - 不用纠结该放哪个分类，直接保存
- 🔍 **语义搜索** - 用自然语言描述，模糊匹配找到相关内容
- 🤖 **AI 描述生成** - 自动生成优化的描述，提升搜索精度
- 💾 **双重存储** - 向量数据库+备份数据库，数据安全有保障
- 🌏 **中文友好** - 使用专门的中文向量模型
- 💻 **双界面** - Web 界面 + 命令行界面

## 📁 项目结构

```
向量知识库/
├── backend/                    # 后端代码
│   ├── __init__.py
│   ├── api.py                 # FastAPI Web 服务
│   ├── main.py                # CLI 命令行界面
│   └── core/                  # 核心模块
│       ├── __init__.py
│       ├── knowledge_base.py  # 向量知识库
│       ├── ai_summarizer.py   # AI 描述生成
│       └── backup_db.py       # 备份数据库
├── frontend/                   # 前端界面
│   └── index.html             # Web 界面
├── docs/                       # 文档
│   ├── README.md              # 主文档
│   ├── AI_MODEL_SETUP.md      # AI 模型设置
│   └── BACKUP_DB_README.md    # 备份数据库说明
├── start_web.py               # Web 服务启动脚本
├── start_cli.py               # CLI 启动脚本
├── requirements.txt           # 依赖配置
└── .gitignore                 # Git 忽略配置
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# Windows 激活
.\venv\Scripts\activate

# Linux/Mac 激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> ⚠️ 首次运行会下载向量模型和 AI 模型（约 3-4GB），请确保网络通畅

### 2. 启动服务

**Web 界面（推荐）：**
```bash
python start_web.py
```
然后访问：http://localhost:8000

**命令行界面：**
```bash
python start_cli.py
```

## 💡 使用示例

### Web 界面

1. **添加笔记**
   - 切换到"添加笔记"模式
   - 输入描述（可选）：一句话总结笔记内容
   - 输入完整笔记内容
   - AI 会自动生成优化的描述

2. **搜索笔记**
   - 切换到"搜索笔记"模式
   - 输入搜索关键词
   - 系统会返回最相关的笔记

### 命令行界面

```
📌 Notes> add                    # 添加笔记
📌 Notes> search 网络穿透         # 搜索笔记
📌 Notes> list                   # 列出所有笔记
📌 Notes> view abc123            # 查看笔记详情
📌 Notes> delete abc123          # 删除笔记
```

## 🔧 配置说明

### 向量模型

默认使用 `BAAI/bge-small-zh-v1.5`，可在 `backend/core/knowledge_base.py` 修改：

```python
self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-zh-v1.5"  # 可替换为其他模型
)
```

### AI 模型

默认使用 `Qwen/Qwen2.5-1.5B-Instruct`，可在 `backend/core/ai_summarizer.py` 修改：

```python
def __init__(self, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):
    # 可替换为其他模型，如 Qwen/Qwen2.5-3B-Instruct
```

## 📊 数据存储

- **向量数据库**: `./knowledge_db/` - 用于语义搜索
- **备份数据库**: `./backup.db` - SQLite，用于数据备份

## 📤 数据导出

```bash
# 导出备份数据
curl http://localhost:8000/api/backup/export > backup.json

# 查看备份统计
curl http://localhost:8000/api/backup/stats
```

## 💻 系统要求

### 最低配置
- CPU: 4核以上
- 内存: 8GB RAM
- 存储: 10GB 可用空间

### 推荐配置
- CPU: 8核以上
- 内存: 16GB RAM
- GPU: NVIDIA GPU（可选，会显著加速 AI 生成）
- 存储: 20GB 可用空间

## 📚 详细文档

- [AI 模型设置说明](docs/AI_MODEL_SETUP.md)
- [备份数据库使用说明](docs/BACKUP_DB_README.md)
- [API 接口文档](http://localhost:8000/docs) - 启动服务后访问

## 🐛 常见问题

### Q: 模型下载失败？
A: 检查网络连接，或使用镜像源：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### Q: 内存不足？
A: 使用更小的模型或禁用 AI 功能，系统会自动降级

### Q: 搜索结果不准确？
A: 添加笔记时填写详细的描述，AI 会生成更准确的搜索关键词

## 🔄 更新日志

### v1.0.0
- ✅ 基础向量搜索功能
- ✅ AI 描述自动生成
- ✅ 双重数据存储（向量+备份）
- ✅ Web 界面 + CLI 界面
- ✅ 完整的文档和示例

## 📝 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**快速启动命令：**
```bash
# Web 界面
python start_web.py

# 命令行界面
python start_cli.py
```
