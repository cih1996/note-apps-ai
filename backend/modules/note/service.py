import uuid
from datetime import datetime
import re
import json
from typing import List, Optional
from backend.core.database import VectorDB, SQLiteDB
from backend.core.ai import get_summarizer
from backend.config import KNOWLEDGE_DB_PATH, BACKUP_DB_PATH

class NoteService:
    def __init__(self):
        self.vector_db = VectorDB(KNOWLEDGE_DB_PATH, "notes")
        self.sqlite_db = SQLiteDB(BACKUP_DB_PATH)
        self.ai_summarizer = get_summarizer()
        self._init_sqlite()

    def _init_sqlite(self):
        self.sqlite_db.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                user_description TEXT,
                ai_description TEXT,
                raw_content TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                char_count INTEGER
            )
        ''')
        self.sqlite_db.execute('''
            CREATE INDEX IF NOT EXISTS idx_created_at ON notes(created_at)
        ''')

    def get_all_tags(self) -> List[str]:
        """获取所有已存在的标签"""
        rows = self.sqlite_db.fetch_all("SELECT tags FROM notes WHERE tags IS NOT NULL AND tags != ''")
        all_tags = set()
        for row in rows:
            if row[0]:
                try:
                    tags = json.loads(row[0])
                    if isinstance(tags, list):
                        all_tags.update(tags)
                except: pass
        return sorted(list(all_tags))

    def add_note(self, content: str, user_description: str = None, tags: List[str] = None) -> dict:
        note_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])
        
        # AI generate summary
        ai_description = ""
        if self.ai_summarizer.is_available():
            try:
                ai_description = self.ai_summarizer.generate_summary(user_description or "", content)
            except Exception as e:
                print(f"AI生成描述失败: {e}")
                ai_description = user_description or content[:100]
        else:
            ai_description = user_description or content[:100]

        # Vector storage
        vector_description = ai_description if ai_description.strip() else user_description
        if not vector_description or not vector_description.strip():
            vector_description = content[:100]
            
        self.vector_db.add(
            ids=[note_id],
            documents=[vector_description],
            metadatas=[{
                "raw_content": content,
                "user_description": user_description or "",
                "ai_description": ai_description or "",
                "tags": tags_json,
                "created_at": created_at,
                "char_count": len(content)
            }]
        )

        # SQLite storage
        self.sqlite_db.execute('''
            INSERT INTO notes 
            (id, user_description, ai_description, raw_content, tags, created_at, char_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (note_id, user_description or "", ai_description or "", content, tags_json, created_at, len(content)))

        return {
            "id": note_id,
            "user_description": user_description or "",
            "ai_description": ai_description or "",
            "tags": tags or []
        }

    def search_notes(self, query: str, top_k: int = 5, filter_tags: List[str] = None) -> List[dict]:
        if self.vector_db.count() == 0:
            return []
        
        # ChromaDB metadata filtering logic for tags
        # Note: If using ChromaDB's built-in filter, we'd use something like:
        # where = {"tags": {"$contains": "tag1"}} if single tag
        # but tags is a JSON string in metadata, so it's a bit complex.
        # For simplicity and flexibility, we'll retrieve more and filter in memory.
        
        actual_k = min(top_k * 5, self.vector_db.count()) # Get more results to account for filtering
        results = self.vector_db.query(query_texts=[query], n_results=actual_k)
        
        notes = []
        if results and results['documents'] and results['documents'][0]:
            query_keywords = self._extract_keywords(query.lower())
            
            for i, vector_desc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i]
                
                # Tag filtering
                note_tags = []
                if metadata.get('tags'):
                    try:
                        note_tags = json.loads(metadata['tags'])
                    except: pass
                
                if filter_tags and len(filter_tags) > 0:
                    if not any(t in note_tags for t in filter_tags):
                        continue

                distance = results['distances'][0][i] if 'distances' in results else 2.0
                vector_similarity = max(0, min(1, 1 - distance / 2))
                
                ai_description = metadata.get('ai_description', '')
                user_description = metadata.get('user_description', '')
                
                ai_keyword_score = self._calculate_keyword_score(query_keywords, ai_description.lower())
                user_keyword_score = self._calculate_keyword_score(query_keywords, user_description.lower())
                
                keyword_score = ai_keyword_score * 0.8 + user_keyword_score * 0.2
                final_similarity = vector_similarity * 0.85 + keyword_score * 0.15
                
                notes.append({
                    "id": results['ids'][0][i],
                    "content": metadata.get('raw_content', ''),
                    "user_description": user_description,
                    "ai_description": ai_description,
                    "tags": note_tags,
                    "metadata": metadata,
                    "similarity": round(final_similarity * 100, 1),
                })
            
            notes.sort(key=lambda x: x['similarity'], reverse=True)
            notes = notes[:top_k]
        
        return notes

    def get_all_notes(self) -> List[dict]:
        rows = self.sqlite_db.fetch_all('SELECT * FROM notes ORDER BY created_at DESC')
        notes = []
        for row in rows:
            tags = []
            try:
                tags = json.loads(row[4] or "[]")
            except: pass
            
            notes.append({
                "id": row[0],
                "user_description": row[1],
                "ai_description": row[2],
                "content": row[3],
                "tags": tags,
                "created_at": row[5],
                "updated_at": row[6],
                "char_count": row[7]
            })
        return notes

    def get_note_by_id(self, note_id: str) -> Optional[dict]:
        row = self.sqlite_db.fetch_one('SELECT * FROM notes WHERE id = ?', (note_id,))
        if row:
            tags = []
            try:
                tags = json.loads(row[4] or "[]")
            except: pass
            
            return {
                "id": row[0],
                "user_description": row[1],
                "ai_description": row[2],
                "content": row[3],
                "tags": tags,
                "created_at": row[5],
                "updated_at": row[6],
                "char_count": row[7]
            }
        return None

    def update_note(self, note_id: str, content: str = None, user_description: str = None, tags: List[str] = None) -> bool:
        old_note = self.get_note_by_id(note_id)
        if not old_note:
            return False
            
        new_content = content if content is not None else old_note['content']
        new_user_desc = user_description if user_description is not None else old_note['user_description']
        new_tags = tags if tags is not None else old_note['tags']
        new_tags_json = json.dumps(new_tags)
        
        # AI generate new summary if content changed
        new_ai_desc = old_note['ai_description']
        if content is not None or user_description is not None:
             if self.ai_summarizer.is_available():
                try:
                    new_ai_desc = self.ai_summarizer.generate_summary(new_user_desc, new_content)
                except Exception:
                    new_ai_desc = new_user_desc or new_content[:100]

        updated_at = datetime.now().isoformat()
        
        # Update Vector
        vector_description = new_ai_desc if new_ai_desc.strip() else new_user_desc
        self.vector_db.delete(ids=[note_id])
        self.vector_db.add(
            ids=[note_id],
            documents=[vector_description],
            metadatas=[{
                "raw_content": new_content,
                "user_description": new_user_desc,
                "ai_description": new_ai_desc,
                "tags": new_tags_json,
                "created_at": old_note['created_at'],
                "updated_at": updated_at,
                "char_count": len(new_content)
            }]
        )

        # Update SQLite
        self.sqlite_db.execute('''
            UPDATE notes SET raw_content = ?, user_description = ?, ai_description = ?, tags = ?, updated_at = ?, char_count = ?
            WHERE id = ?
        ''', (new_content, new_user_desc, new_ai_desc, new_tags_json, updated_at, len(new_content), note_id))
        
        return True

    def delete_note(self, note_id: str) -> bool:
        self.vector_db.delete(ids=[note_id])
        self.sqlite_db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        return True

    def _extract_keywords(self, text: str) -> list:
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text)
        return [w for w in words if len(w) >= 2]

    def _calculate_keyword_score(self, query_keywords: list, doc_text: str) -> float:
        if not query_keywords or not doc_text: return 0.0
        matched_count = 0
        total_score = 0.0
        for keyword in query_keywords:
            if keyword in doc_text:
                matched_count += 1
                count = doc_text.count(keyword)
                freq_score = min(1.0, count / 10.0)
                total_score += freq_score
        if matched_count == 0: return 0.0
        match_rate = matched_count / len(query_keywords)
        avg_freq = total_score / len(query_keywords)
        return match_rate * 0.6 + avg_freq * 0.4

