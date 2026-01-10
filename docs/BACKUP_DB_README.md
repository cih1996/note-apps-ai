# 备份数据库说明

## 📋 功能概述

系统现在会自动将笔记的原始数据保存到 SQLite 备份数据库中，**不进行向量化**，仅用于数据备份和恢复。

### 存储的数据

备份数据库存储以下3个字段的原始数据：

1. **user_description** - 用户输入的描述
2. **ai_description** - AI生成的描述  
3. **raw_content** - 原始笔记内容

## 📁 数据库文件

- **文件位置**: `./backup.db`
- **数据库类型**: SQLite
- **文件大小**: 根据笔记数量而定，通常很小（几MB到几十MB）

## 🔄 自动同步

系统会在以下操作时自动同步备份数据库：

- ✅ **添加笔记**：自动保存到备份数据库
- ✅ **删除笔记**：自动从备份数据库删除
- ⚠️ **更新笔记**：暂不支持（未来可扩展）

## 📤 导出备份数据

### 方法1：通过API导出

```bash
# 获取备份数据（JSON格式）
curl http://localhost:8000/api/backup/export > backup.json

# 查看备份统计
curl http://localhost:8000/api/backup/stats
```

### 方法2：使用Python脚本导出

```python
from backup_db import get_backup_db

backup_db = get_backup_db()

# 导出为JSON文件
backup_db.export_to_json("./backup_export.json")

# 获取所有笔记
notes = backup_db.get_all_notes()
print(f"共有 {len(notes)} 条备份记录")
```

### 方法3：直接访问SQLite数据库

```bash
# 使用SQLite命令行工具
sqlite3 backup.db

# 查看所有笔记
SELECT * FROM notes;

# 导出为CSV
.mode csv
.output backup.csv
SELECT * FROM notes;
```

## 🔍 查看备份数据

### Python代码示例

```python
from backup_db import get_backup_db

backup_db = get_backup_db()

# 获取所有笔记
all_notes = backup_db.get_all_notes()
for note in all_notes:
    print(f"ID: {note['id']}")
    print(f"用户描述: {note['user_description']}")
    print(f"AI描述: {note['ai_description']}")
    print(f"原始内容: {note['raw_content'][:100]}...")
    print("-" * 50)

# 获取单条笔记
note = backup_db.get_note("abc123")
if note:
    print(note)

# 获取笔记总数
count = backup_db.count()
print(f"共有 {count} 条备份记录")
```

## 💾 备份和恢复

### 备份数据库文件

```bash
# Windows
copy backup.db backup_20241228.db

# Linux/Mac
cp backup.db backup_20241228.db
```

### 恢复数据库

```bash
# 替换数据库文件即可
cp backup_20241228.db backup.db
```

## 📊 数据库结构

```sql
CREATE TABLE notes (
    id TEXT PRIMARY KEY,              -- 笔记ID（与向量数据库一致）
    user_description TEXT,            -- 用户描述
    ai_description TEXT,              -- AI描述
    raw_content TEXT NOT NULL,        -- 原始内容
    created_at TEXT NOT NULL,         -- 创建时间
    updated_at TEXT,                  -- 更新时间（暂未使用）
    char_count INTEGER                -- 字符数
);

CREATE INDEX idx_created_at ON notes(created_at);
```

## 🔧 维护操作

### 清理旧数据

```python
from backup_db import get_backup_db
from datetime import datetime, timedelta

backup_db = get_backup_db()
all_notes = backup_db.get_all_notes()

# 删除30天前的笔记（示例）
cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
for note in all_notes:
    if note['created_at'] < cutoff_date:
        backup_db.delete_note(note['id'])
```

### 数据迁移

```python
from backup_db import BackupDatabase

# 创建新的备份数据库
new_db = BackupDatabase("./backup_new.db")

# 从旧数据库复制数据
old_db = BackupDatabase("./backup.db")
old_notes = old_db.get_all_notes()

for note in old_notes:
    new_db.add_note(
        note_id=note['id'],
        raw_content=note['raw_content'],
        user_description=note['user_description'],
        ai_description=note['ai_description']
    )
```

## ⚠️ 注意事项

1. **备份数据库独立于向量数据库**
   - 向量数据库用于搜索匹配
   - 备份数据库仅用于数据备份
   - 两者数据同步，但功能独立

2. **数据一致性**
   - 如果备份数据库操作失败，不会影响主功能
   - 系统会显示警告，但继续正常运行

3. **文件安全**
   - 备份数据库包含所有原始数据
   - 请妥善保管 `backup.db` 文件
   - 建议定期备份到安全位置

4. **性能影响**
   - SQLite 操作很快，几乎不影响性能
   - 如果笔记数量很大（>10万条），可能需要优化

## 🐛 故障排除

### 问题1：备份数据库文件损坏

**解决方案**：
```bash
# 删除损坏的文件，系统会自动重建
rm backup.db
# 重新启动程序
```

### 问题2：备份数据库不同步

**解决方案**：
- 检查是否有写入权限
- 查看控制台是否有错误信息
- 手动同步：从向量数据库重新导出

### 问题3：文件过大

**解决方案**：
```python
# 导出为JSON后压缩
import gzip
import json

backup_db = get_backup_db()
notes = backup_db.get_all_notes()

with gzip.open('backup.json.gz', 'wt', encoding='utf-8') as f:
    json.dump(notes, f, ensure_ascii=False, indent=2)
```

## 📚 相关文件

- `backup_db.py` - 备份数据库模块
- `knowledge_base.py` - 向量知识库（自动同步）
- `api.py` - API接口（包含导出接口）

