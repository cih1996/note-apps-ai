# 配置文件说明

## 📝 配置文件位置

项目根目录的 `.env` 文件

## 🔧 配置项说明

### 1. HuggingFace 离线模式（解决联网问题）

```env
# 启用离线模式，不联网，使用本地已下载的模型
HF_HUB_OFFLINE=true
```

**重要说明：**
- 设置为 `true` 后，程序不会尝试连接 HuggingFace
- 模型会从本地缓存加载
- 默认缓存位置：
  - Windows: `C:\Users\你的用户名\.cache\huggingface`
  - Linux/Mac: `~/.cache/huggingface`

### 2. 向量模型配置

```env
# 使用 HuggingFace 模型名称（会从缓存加载）
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5

# 或使用本地路径（如果模型在其他位置）
EMBEDDING_MODEL_PATH=D:/models/bge-small-zh-v1.5
```

**模型选项：**
- `BAAI/bge-small-zh-v1.5` - 推荐，中文效果好
- `BAAI/bge-base-zh-v1.5` - 更准确但更慢
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` - 多语言

### 3. AI 模型配置

```env
# AI 模型名称
AI_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct

# 或使用本地路径
AI_MODEL_PATH=D:/models/Qwen2.5-1.5B-Instruct

# 禁用 AI 功能（加快启动速度）
DISABLE_AI_MODEL=true
```

**模型选项：**
- `Qwen/Qwen2.5-1.5B-Instruct` - 推荐，1.5B参数
- `Qwen/Qwen2.5-3B-Instruct` - 更准确，3B参数
- `THUDM/chatglm3-2b` - 另一个选择

### 4. 数据存储路径

```env
KNOWLEDGE_DB_PATH=./knowledge_db
BACKUP_DB_PATH=./backup.db
```

可以修改为其他路径，如：
```env
KNOWLEDGE_DB_PATH=D:/data/knowledge_db
BACKUP_DB_PATH=D:/data/backup.db
```

### 5. Web 服务配置

```env
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

修改端口（如果8000被占用）：
```env
WEB_PORT=8001
```

## 🚀 快速配置场景

### 场景1：完全离线使用（已下载模型）

```env
HF_HUB_OFFLINE=true
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
AI_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
```

### 场景2：模型在自定义位置

```env
HF_HUB_OFFLINE=true
EMBEDDING_MODEL_PATH=D:/my_models/bge-small-zh-v1.5
AI_MODEL_PATH=D:/my_models/Qwen2.5-1.5B-Instruct
```

### 场景3：不使用 AI 功能（更快）

```env
HF_HUB_OFFLINE=true
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
DISABLE_AI_MODEL=true
```

### 场景4：需要下载模型

```env
HF_HUB_OFFLINE=false
HF_ENDPOINT=https://hf-mirror.com
EMBEDDING_MODEL_NAME=BAAI/bge-small-zh-v1.5
AI_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct
```

## 🔍 查找已下载的模型

### Windows

打开文件管理器，输入地址：
```
%USERPROFILE%\.cache\huggingface\hub
```

### Linux/Mac

```bash
ls ~/.cache/huggingface/hub
```

模型文件夹格式：
- `models--BAAI--bge-small-zh-v1.5`
- `models--Qwen--Qwen2.5-1.5B-Instruct`

## ⚠️ 常见问题

### Q1: 还是提示联网？

**检查：**
1. `.env` 文件是否在项目根目录
2. `HF_HUB_OFFLINE=true` 是否正确
3. 模型是否已下载到缓存目录

**解决：**
```env
# 确保这一行存在且为 true
HF_HUB_OFFLINE=true
```

### Q2: 找不到模型？

**检查模型是否存在：**
```python
import os
cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
print(os.listdir(cache_dir))
```

**如果模型不存在，设置为 false 下载：**
```env
HF_HUB_OFFLINE=false
HF_ENDPOINT=https://hf-mirror.com
```

### Q3: 代理错误？

配置文件会自动禁用代理，如果还有问题：

**手动设置：**
```bash
# Windows PowerShell
$env:NO_PROXY="*"
$env:HTTP_PROXY=""
$env:HTTPS_PROXY=""

# Linux/Mac
export NO_PROXY="*"
export HTTP_PROXY=""
export HTTPS_PROXY=""
```

### Q4: 模型路径怎么填？

**Windows:**
```env
EMBEDDING_MODEL_PATH=D:/models/bge-small-zh-v1.5
# 或
EMBEDDING_MODEL_PATH=D:\\models\\bge-small-zh-v1.5
```

**Linux/Mac:**
```env
EMBEDDING_MODEL_PATH=/home/user/models/bge-small-zh-v1.5
```

## 📚 相关文档

- [主要文档](../README.md)
- [AI 模型设置](AI_MODEL_SETUP.md)
- [快速入门](../QUICK_START.md)

