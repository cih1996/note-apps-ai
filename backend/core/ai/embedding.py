import os
from sentence_transformers import SentenceTransformer
from backend.config import LOCAL_FILES_ONLY
import chromadb.api.types as types

class EmbeddingModel:
    def __init__(self, model_name: str = None, model_path: str = None):
        if model_name is None:
            from backend.config import EMBEDDING_MODEL_NAME
            model_name = EMBEDDING_MODEL_NAME
        
        if model_path is None:
            from backend.config import EMBEDDING_MODEL_PATH
            model_path = EMBEDDING_MODEL_PATH
            
        self.model_name = model_name
        self.model_path = model_path
        
        load_kwargs = {
            'device': 'cpu',
        }
        
        if LOCAL_FILES_ONLY:
            load_kwargs['local_files_only'] = True
            
        if self.model_path and os.path.exists(self.model_path):
            if os.path.isdir(self.model_path):
                load_kwargs['cache_folder'] = os.path.dirname(self.model_path)
        
        try:
            self.model = SentenceTransformer(self.model_name, **load_kwargs)
        except Exception as e:
            print(f"❌ 向量模型加载失败: {e}")
            raise

    def encode(self, texts):
        return self.model.encode(texts, show_progress_bar=False)

# Custom embedding function for ChromaDB
class ChromaEmbeddingFunction(types.EmbeddingFunction):
    def __init__(self, model: EmbeddingModel):
        self.model = model
    
    def name(self) -> str:
        return "ChromaEmbeddingFunction"
    
    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        embeddings = self.model.encode(input)
        return embeddings.tolist()
    
    def embed_documents(self, input):
        return self.__call__(input)
    
    def embed_query(self, input):
        if isinstance(input, str):
            embeddings = self.model.encode([input])
            return embeddings[0].tolist()
        else:
            embeddings = self.model.encode(input)
            return embeddings.tolist()

