# AI 描述生成功能说明

## 📋 功能概述

系统现在支持使用本地AI模型自动生成笔记描述，提升搜索匹配精度。

### 工作流程

1. **用户输入**：
   - 用户描述（可选）：一句话总结笔记
   - 原始内容：完整的笔记内容

2. **AI处理**：
   - 系统使用本地AI模型（Qwen2.5-1.5B-Instruct）
   - 结合用户描述和原始内容，生成优化的AI描述

3. **向量存储**：
   - **AI描述**：用于向量化（优先级最高）
   - **用户描述**：辅助匹配
   - **原始内容**：不参与向量匹配，仅作为结果展示

4. **搜索匹配**：
   - 优先匹配AI描述（权重 80%）
   - 其次匹配用户描述（权重 20%）
   - 原始内容不参与向量匹配

## 🚀 安装AI模型

### 方法1：自动下载（推荐）

首次运行时，系统会自动从 Hugging Face 下载模型（约3GB）。

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 运行后端，会自动下载模型
python api.py
```

### 方法2：手动下载

如果自动下载失败，可以手动下载：

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-1.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
```

### 方法3：使用其他模型

如果你想使用其他模型，修改 `ai_summarizer.py`：

```python
# 推荐的中文小模型：
# - Qwen/Qwen2.5-1.5B-Instruct (1.5B, 推荐)
# - Qwen/Qwen2.5-3B-Instruct (3B, 更准确但更慢)
# - THUDM/chatglm3-2b (2B, 中文支持好)
```

## 💻 系统要求

### 最低配置
- **CPU**: 4核以上
- **内存**: 8GB RAM
- **存储**: 5GB 可用空间（用于模型文件）

### 推荐配置
- **CPU**: 8核以上
- **内存**: 16GB RAM
- **GPU**: NVIDIA GPU（可选，会显著加速）
- **存储**: 10GB 可用空间

## 🔧 配置说明

### 禁用AI功能

如果不想使用AI功能，系统会自动降级：
- 使用用户描述（如果提供）
- 否则使用原始内容的前100字符

### 调整模型参数

编辑 `ai_summarizer.py` 中的生成参数：

```python
generated_ids = self.model.generate(
    **model_inputs,
    max_new_tokens=100,      # 最大生成长度
    temperature=0.7,         # 创造性（0-1，越高越随机）
    do_sample=True,
    top_p=0.9                # 核采样参数
)
```

## 📊 性能优化

### GPU加速

如果有NVIDIA GPU，系统会自动使用GPU加速：

```bash
# 检查CUDA是否可用
python -c "import torch; print(torch.cuda.is_available())"
```

### 内存优化

如果内存不足，可以：

1. **使用更小的模型**：
   ```python
   model_name = "Qwen/Qwen2.5-0.5B-Instruct"  # 更小但效果略差
   ```

2. **使用量化模型**（需要额外配置）

3. **禁用AI功能**：系统会自动降级到用户描述

## 🐛 故障排除

### 问题1：模型下载失败

**解决方案**：
- 检查网络连接
- 使用镜像源：
  ```bash
  export HF_ENDPOINT=https://hf-mirror.com
  ```

### 问题2：内存不足

**解决方案**：
- 关闭其他程序释放内存
- 使用更小的模型
- 系统会自动降级到用户描述

### 问题3：生成速度慢

**解决方案**：
- 使用GPU加速（如果有）
- 使用更小的模型
- 调整 `max_new_tokens` 参数

## 📝 使用示例

### 添加笔记

```javascript
// 前端调用
POST /api/notes
{
  "content": "nohup ./frps -c frps.ini > frps.log 2>&1 &\nfrp映射命令行",
  "description": "frp网络穿透命令"
}

// 返回
{
  "id": "abc123",
  "status": "success",
  "user_description": "frp网络穿透命令",
  "ai_description": "FRP内网穿透服务启动命令，使用nohup后台运行并输出日志"
}
```

### 搜索笔记

搜索时会优先匹配AI描述，匹配度更高。

## 🔄 升级说明

### 从旧版本升级

如果你之前已经有笔记数据，需要：

1. **备份数据**：备份 `knowledge_db` 目录
2. **重新添加笔记**：新笔记会自动使用AI描述
3. **旧笔记**：会继续使用原有描述，不影响使用

## 📚 相关文档

- [Qwen2.5 模型文档](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
- [Transformers 文档](https://huggingface.co/docs/transformers)

