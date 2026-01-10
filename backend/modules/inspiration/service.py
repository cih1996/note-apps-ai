import uuid
from datetime import datetime
import re
import json
from typing import List, Optional
from backend.core.database import VectorDB, SQLiteDB
from backend.core.ai import get_summarizer
from backend.config import INSPIRATION_DB_PATH, BACKUP_DB_PATH

class InspirationService:
    def __init__(self):
        # Use a separate vector database for inspiration
        self.vector_db = VectorDB(INSPIRATION_DB_PATH, "inspiration")
        self.sqlite_db = SQLiteDB(BACKUP_DB_PATH)
        self.ai_summarizer = get_summarizer()
        self._init_sqlite()

    def _init_sqlite(self):
        # We'll use a separate table in the same backup.db or a different one. 
        # Let's use the same backup.db but a different table 'inspirations'.
        self.sqlite_db.execute('''
            CREATE TABLE IF NOT EXISTS inspirations (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                title TEXT,
                theme TEXT,
                summary TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')

    def add_inspiration(self, content: str) -> dict:
        inspiration_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()
        
        # AI as "Interpreter"
        ai_data = self._interpret_with_ai(content)
        
        # Save to SQLite (Original content + AI analysis)
        self.sqlite_db.execute('''
            INSERT INTO inspirations 
            (id, content, title, theme, summary, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            inspiration_id, 
            content, 
            ai_data['title'], 
            ai_data['theme'], 
            ai_data['summary'], 
            json.dumps(ai_data['tags'], ensure_ascii=False),
            created_at
        ))

        # Vectorize AI analysis for future retrieval (awakening)
        # We vectorize a combination of title, theme, and summary
        vector_text = f"标题: {ai_data['title']}\n主题: {ai_data['theme']}\n摘要: {ai_data['summary']}\n标签: {' '.join(ai_data['tags'])}"
        
        self.vector_db.add(
            ids=[inspiration_id],
            documents=[vector_text],
            metadatas=[{
                "id": inspiration_id,
                "title": ai_data['title'],
                "theme": ai_data['theme'],
                "tags": json.dumps(ai_data['tags'], ensure_ascii=False),
                "created_at": created_at
            }]
        )

        return {
            "id": inspiration_id,
            "title": ai_data['title'],
            "theme": ai_data['theme'],
            "summary": ai_data['summary'],
            "tags": ai_data['tags']
        }

    def _interpret_with_ai(self, content: str) -> dict:
        default_data = {
            "title": "未命名灵感",
            "theme": "通用",
            "summary": content[:100] + "...",
            "tags": ["灵感"]
        }
        
        if not self.ai_summarizer.is_available():
            return default_data

        system_prompt = (
            "你是一个灵感解释器。用户会输入一段感性、甚至混乱的长篇自诉。"
            "你的任务是作为“旁白”和“索引员”，在不修改原始内容的前提下，提炼出以下信息："
            "1. 标题 (title): 10字以内，捕捉灵感的核心神韵。"
            "2. 主题 (theme): 5字以内，定义灵感围绕的核心领域。"
            "3. 摘要 (summary): 50字以内，客观描述这段自诉在表达什么。"
            "4. 弱标签 (tags): 3-5个词，用于未来语义联动。"
            "请直接以 JSON 格式返回，不要包含任何其他文字。"
            "格式示例: {\"title\": \"...\", \"theme\": \"...\", \"summary\": \"...\", \"tags\": [\"...\", \"...\"]}"
        )
        
        user_prompt = f"内容如下：\n{content}"
        
        try:
            response = self.ai_summarizer.generate(system_prompt, user_prompt, max_tokens=300)
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Validate keys
                required = ["title", "theme", "summary", "tags"]
                if all(k in data for k in required):
                    return data
            return default_data
        except Exception as e:
            print(f"AI解释灵感失败: {e}")
            return default_data

    def search_inspirations(self, query: str, top_k: int = 5) -> List[dict]:
        if self.vector_db.count() == 0:
            return []
        
        results = self.vector_db.query(query_texts=[query], n_results=top_k)
        
        inspirations = []
        if results and results['ids'] and results['ids'][0]:
            for i, inspiration_id in enumerate(results['ids'][0]):
                # Fetch full data from SQLite
                row = self.sqlite_db.fetch_one('SELECT * FROM inspirations WHERE id = ?', (inspiration_id,))
                if row:
                    distance = results['distances'][0][i] if 'distances' in results else 2.0
                    similarity = max(0, min(1, 1 - distance / 2))
                    
                    inspirations.append({
                        "id": row[0],
                        "content": row[1],
                        "title": row[2],
                        "theme": row[3],
                        "summary": row[4],
                        "tags": json.loads(row[5]),
                        "created_at": row[6],
                        "similarity": round(similarity * 100, 1)
                    })
        
        return inspirations

    def get_all_inspirations(self, limit: int = 20, offset: int = 0) -> List[dict]:
        rows = self.sqlite_db.fetch_all(
            'SELECT * FROM inspirations ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )
        inspirations = []
        for row in rows:
            inspirations.append({
                "id": row[0],
                "content": row[1],
                "title": row[2],
                "theme": row[3],
                "summary": row[4],
                "tags": json.loads(row[5]),
                "created_at": row[6]
            })
        return inspirations

    def delete_inspiration(self, inspiration_id: str) -> bool:
        self.vector_db.delete(ids=[inspiration_id])
        self.sqlite_db.execute('DELETE FROM inspirations WHERE id = ?', (inspiration_id,))
        return True

