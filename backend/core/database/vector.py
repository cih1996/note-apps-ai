import chromadb
from backend.core.ai import ChromaEmbeddingFunction, EmbeddingModel

class VectorDB:
    def __init__(self, db_path: str, collection_name: str):
        print(db_path)
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = EmbeddingModel()
        self.embedding_fn = ChromaEmbeddingFunction(self.embedding_model)
 
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add(self, ids, documents, metadatas):
        return self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, query_texts, n_results=5):
        return self.collection.query(query_texts=query_texts, n_results=n_results)

    def get(self, ids=None, include=None):
        return self.collection.get(ids=ids, include=include or ["documents", "metadatas"])

    def delete(self, ids):
        return self.collection.delete(ids=ids)

    def count(self):
        return self.collection.count()

    def update(self, ids, documents=None, metadatas=None):
        # ChromaDB update
        return self.collection.update(ids=ids, documents=documents, metadatas=metadatas)

