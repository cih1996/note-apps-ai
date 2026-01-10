import uuid
from datetime import datetime
import json
import re
from typing import List, Optional
from backend.core.database import SQLiteDB
from backend.core.ai import get_summarizer
from backend.config import TODO_DB_PATH

class TodoService:
    def __init__(self):
        self.sqlite_db = SQLiteDB(TODO_DB_PATH)
        self.ai_summarizer = get_summarizer()
        self._init_sqlite()

    def _init_sqlite(self):
        self.sqlite_db.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                task TEXT NOT NULL,
                priority TEXT,
                status TEXT DEFAULT 'pending',
                subtasks TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                completed_at TEXT,
                reminder_at TEXT
            )
        ''')
        # Migrations
        try:
            self.sqlite_db.execute('ALTER TABLE todos ADD COLUMN completed_at TEXT')
        except:
            pass 
        try:
            self.sqlite_db.execute('ALTER TABLE todos ADD COLUMN reminder_at TEXT')
        except:
            pass
        try:
            self.sqlite_db.execute('ALTER TABLE todos ADD COLUMN subtasks TEXT')
        except:
            pass

    def parse_with_ai(self, content: str) -> List[dict]:
        """
        Use AI to parse natural language into multiple structured todo items with optional subtasks.
        """
        if not self.ai_summarizer.is_available():
            return [{"task": content, "priority": "近期", "subtasks": []}]

        system_prompt = (
            "你是一个待办事项整理助手。用户会输入一段任务描述。"
            "请将其拆解为待办事项，并为复杂任务生成详细的子步骤。\n\n"
            "规则：\n"
            "1. 优先级可选：'紧急', '近期', '长期', '待定'\n"
            "2. 如果任务比较复杂，需要多个步骤完成，请在 subtasks 数组中列出所有子步骤\n"
            "3. 如果任务很简单，subtasks 可以为空数组\n"
            "4. 每个子步骤只需要 task 字段，描述要做什么\n\n"
            "请直接以 JSON 数组格式返回，不要包含任何其他文字。\n\n"
            "格式示例：\n"
            "[{\n"
            '  "task": "完成项目报告",\n'
            '  "priority": "紧急",\n'
            '  "subtasks": [\n'
            '    {"task": "收集数据资料"},\n'
            '    {"task": "撰写初稿"},\n'
            '    {"task": "审阅修改"},\n'
            '    {"task": "提交报告"}\n'
            "  ]\n"
            "}, {\n"
            '  "task": "买菜",\n'
            '  "priority": "近期",\n'
            '  "subtasks": []\n'
            "}]"
        )
        
        user_prompt = f"内容如下：\n{content}"
        
        try:
            response = self.ai_summarizer.generate(system_prompt, user_prompt, max_tokens=800)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                items = json.loads(json_match.group())
                # Ensure subtasks field exists
                for item in items:
                    if 'subtasks' not in item:
                        item['subtasks'] = []
                return items
            return [{"task": content, "priority": "近期", "subtasks": []}]
        except Exception as e:
            print(f"AI解析待办失败: {e}")
            return [{"task": content, "priority": "近期", "subtasks": []}]

    def add_todos(self, items: List[dict]) -> bool:
        created_at = datetime.now().isoformat()
        for item in items:
            todo_id = str(uuid.uuid4())[:8]
            
            # Process subtasks: add id and status to each
            subtasks = item.get('subtasks', [])
            processed_subtasks = []
            for subtask in subtasks:
                if isinstance(subtask, dict):
                    processed_subtasks.append({
                        'id': str(uuid.uuid4())[:8],
                        'task': subtask.get('task', ''),
                        'status': 'pending',
                        'completed_at': None
                    })
            
            subtasks_json = json.dumps(processed_subtasks)
            
            self.sqlite_db.execute('''
                INSERT INTO todos (id, task, priority, status, subtasks, created_at, reminder_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (todo_id, item['task'], item['priority'], 'pending', subtasks_json, created_at, item.get('reminder_at')))
        return True

    def get_all_todos(self) -> List[dict]:
        rows = self.sqlite_db.fetch_all('SELECT * FROM todos ORDER BY created_at DESC')
        todos = []
        for row in rows:
            subtasks = []
            try:
                if len(row) > 4 and row[4]:
                    subtasks = json.loads(row[4])
            except:
                pass
            
            todos.append({
                "id": row[0],
                "task": row[1],
                "priority": row[2],
                "status": row[3],
                "subtasks": subtasks,
                "created_at": row[5],
                "updated_at": row[6],
                "completed_at": row[7] if len(row) > 7 else None,
                "reminder_at": row[8] if len(row) > 8 else None
            })
        return todos

    def update_status(self, todo_id: str, status: str, completed_at: Optional[str] = None) -> bool:
        updated_at = datetime.now().isoformat()
        if status == "completed":
            # If no completed_at provided, use current time
            final_completed_at = completed_at or updated_at
            self.sqlite_db.execute('''
                UPDATE todos SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?
            ''', (status, updated_at, final_completed_at, todo_id))
        else:
            self.sqlite_db.execute('''
                UPDATE todos SET status = ?, updated_at = ?, completed_at = NULL WHERE id = ?
            ''', (status, updated_at, todo_id))
        return True

    def update_subtask_status(self, todo_id: str, subtask_id: str, status: str, completed_at: Optional[str] = None) -> bool:
        """Update a subtask's status and check if all subtasks are completed"""
        updated_at = datetime.now().isoformat()
        
        # Get current todo with subtasks
        row = self.sqlite_db.fetch_one('SELECT subtasks, status FROM todos WHERE id = ?', (todo_id,))
        if not row:
            return False
        
        
        try:
            subtasks = json.loads(row[0]) if row[0] else []
            todo_status = row[1]
        except:
            subtasks = []
        
        # Update the specific subtask
        for subtask in subtasks:
            if subtask['id'] == subtask_id:
                subtask['status'] = status
                if status == 'completed':
                    subtask['completed_at'] = completed_at or updated_at
                else:
                    subtask['completed_at'] = None
                break
        
        # Check if all subtasks are completed
        all_completed = len(subtasks) > 0 and all(st['status'] == 'completed' for st in subtasks)
        
        # Update the todo
        if all_completed:
            self.sqlite_db.execute('''
                UPDATE todos SET subtasks = ?, status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?
            ''', (json.dumps(subtasks), updated_at, updated_at, todo_id))
        else:
            if(todo_status == 'completed'):
                todo_status = 'pending'
            self.sqlite_db.execute('''
                UPDATE todos SET subtasks = ?, status = ?, updated_at = ? WHERE id = ?
            ''', (json.dumps(subtasks), todo_status, updated_at, todo_id))
        
        return True

    def update_info(self, todo_id: str, task: str, priority: str) -> bool:
        updated_at = datetime.now().isoformat()
        self.sqlite_db.execute('''
            UPDATE todos SET task = ?, priority = ?, updated_at = ? WHERE id = ?
        ''', (task, priority, updated_at, todo_id))
        return True

    def delete_todo(self, todo_id: str) -> bool:
        self.sqlite_db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        return True

