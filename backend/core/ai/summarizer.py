"""
AI 描述生成模块
使用本地小模型生成描述
"""

import os
import logging
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from backend.config import LOCAL_FILES_ONLY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AISummarizer:
    """AI 描述生成器"""
    
    def __init__(self, model_name: str = None, model_path: str = None):
        """
        初始化AI模型
        
        Args:
            model_name: 模型名称
            model_path: 模型本地路径（可选）
        """
        # 从配置文件读取
        if model_name is None:
            from backend.config import AI_MODEL_NAME, AI_MODEL_PATH, DISABLE_AI_MODEL
            
            # 如果禁用AI模型，直接返回
            if DISABLE_AI_MODEL:
                logger.info("⚠️  AI 模型已禁用（配置文件设置）")
                self.model = None
                self.tokenizer = None
                return
            
            model_name = AI_MODEL_PATH if AI_MODEL_PATH else AI_MODEL_NAME
        elif model_path:
            model_name = model_path  # 使用本地路径
        
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
    
    def _load_model(self):
        """加载模型"""
        try:
            from backend.config import AI_MODEL_PATH
            
            logger.info(f"正在加载AI模型: {self.model_name}")
            logger.info(f"使用设备: {self.device}")
            
            if LOCAL_FILES_ONLY:
                logger.info("✅ 本地文件优先模式（优先使用缓存，必要时访问元数据）")
            else:
                logger.info("⚠️  在线模式（允许下载模型）")
            
            # 准备加载参数
            load_kwargs = {
                'trust_remote_code': True,
                'low_cpu_mem_usage': True,
            }
            
            # 设置离线模式
            if LOCAL_FILES_ONLY:
                load_kwargs['local_files_only'] = True
                logger.info("  - 启用 local_files_only=True")
            
            # 如果指定了模型路径
            if AI_MODEL_PATH and os.path.exists(AI_MODEL_PATH):
                if os.path.isdir(AI_MODEL_PATH):
                    load_kwargs['cache_dir'] = os.path.dirname(AI_MODEL_PATH)
                    logger.info(f"  - 使用模型目录: {AI_MODEL_PATH}")
            
            logger.info("⚠️  首次加载可能需要几分钟，请耐心等待...")
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                **load_kwargs
            )
            
            # 加载模型（使用半精度以节省显存）
            model_kwargs = load_kwargs.copy()
            model_kwargs['torch_dtype'] = torch.float16 if self.device == "cuda" else torch.float32
            if self.device == "cuda":
                model_kwargs['device_map'] = "auto"
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            self.model.eval()
            logger.info("✅ AI模型加载完成，可以开始使用！")
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            logger.warning("将使用备用方案：直接使用用户描述")
            self.model = None
            self.tokenizer = None
    
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 100) -> str:
        """
        通用AI生成方法
        """
        if not self.model or not self.tokenizer:
            return ""
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9
                )
            
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            return response.strip()
        except Exception as e:
            logger.error(f"AI生成失败: {e}")
            return ""

    def generate_summary(self, user_description: str, raw_content: str) -> str:
        """
        生成AI描述
        
        Args:
            user_description: 用户自己输入的描述
            raw_content: 原始笔记内容
            
        Returns:
            AI生成的描述
        """
        # 如果模型未加载，直接返回用户描述
        if not self.model or not self.tokenizer:
            return user_description if user_description.strip() else raw_content[:100]
        
        try:
            # 构建提示词
            prompt = f"用户描述：{user_description}\n\n笔记内容：\n{raw_content[:500]} "
            
            # 构建对话格式（Qwen2.5格式）
            messages = [
                {"role": "system", "content": "你的职责是为笔记内容生成标题方便检索,如果用户描述不够精准,结合笔记内容生成，不带“用户”等字样，不可包含数据信息，10-30字内。"},
                {"role": "user", "content": prompt}
            ]
            
            # 编码输入
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            model_inputs = self.tokenizer([text], return_tensors="pt").to(self.device)
            
            # 生成
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **model_inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9
                )
            
            # 解码输出
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # 清理输出
            response = response.strip()
            
            # 如果生成的内容太短或为空，使用用户描述
            if len(response) < 10:
                return user_description if user_description.strip() else raw_content[:100]
            
            return response
            
        except Exception as e:
            logger.error(f"生成描述失败: {e}")
            # 失败时返回用户描述
            return user_description if user_description.strip() else raw_content[:100]
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        return self.model is not None and self.tokenizer is not None


# 全局单例
_summarizer_instance = None

def get_summarizer() -> AISummarizer:
    """获取AI摘要器单例"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = AISummarizer()
    return _summarizer_instance

