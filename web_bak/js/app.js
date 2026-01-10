// Vector Notes - Vue 应用主逻辑
const { createApp, ref, onUpdated, nextTick } = Vue;

createApp({
    setup() {
        const currentTab = ref('note'); // 'note' or 'inspiration'
        const input = ref('');
        const loading = ref(false);
        const messages = ref([]);
        const messageBox = ref(null);
        const textarea = ref(null);
        
        // 灵感相关状态
        const inspirationInput = ref('');
        const inspirationLoading = ref(false);
        const inspirationMessages = ref([]);
        const inspirationMessageBox = ref(null);
        const addingInspiration = ref(false);
        const inspirationForm = ref({ content: '' });
        const inspirationSaving = ref(false);
        const viewingInspiration = ref(null);
        
        // 添加笔记相关状态
        const addingNote = ref(false);
        const addForm = ref({
            user_description: '',
            content: ''
        });
        
        // 查看相关状态
        const viewingNote = ref(null);
        
        // 编辑相关状态
        const editingNote = ref(null);
        const editForm = ref({
            user_description: '',
            content: ''
        });
        const saving = ref(false);
        const deleting = ref(false);

        const scrollToBottom = async () => {
            await nextTick();
            const box = currentTab.value === 'note' ? messageBox.value : inspirationMessageBox.value;
            if (box) {
                box.scrollTop = box.scrollHeight;
            }
        };

        // --- 灵感模块方法 ---
        const openInspirationModal = () => {
            addingInspiration.value = true;
            inspirationForm.value = { content: '' };
        };

        const cancelInspiration = () => {
            if (inspirationForm.value.content.trim() && !confirm('确定要放弃这段灵感吗？')) return;
            addingInspiration.value = false;
        };

        const saveInspiration = async () => {
            if (!inspirationForm.value.content.trim()) return;
            inspirationSaving.value = true;
            try {
                const res = await fetch('/api/inspiration/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: inspirationForm.value.content })
                });
                if (!res.ok) throw new Error('保存灵感失败');
                const data = await res.json();
                
                // 添加自诉内容到聊天流
                inspirationMessages.value.push({ 
                    role: 'user', 
                    content: inspirationForm.value.content,
                    time: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
                });
                
                // 添加AI解释结果
                inspirationMessages.value.push({
                    role: 'assistant',
                    type: 'interpreter',
                    data: data
                });
                
                addingInspiration.value = false;
                await scrollToBottom();
            } catch (err) {
                alert(err.message);
            } finally {
                inspirationSaving.value = false;
            }
        };

        const handleInspirationSearch = async () => {
            const text = inspirationInput.value.trim();
            if (!text || inspirationLoading.value) return;

            inspirationMessages.value.push({ role: 'user', content: `[唤醒相关灵感]: ${text}` });
            inspirationInput.value = '';
            inspirationLoading.value = true;
            await scrollToBottom();

            try {
                const res = await fetch('/api/inspiration/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: text, top_k: 4 })
                });
                if (!res.ok) throw new Error('搜索灵感失败');
                const results = await res.json();
                
                if (results.length === 0) {
                    inspirationMessages.value.push({ role: 'assistant', content: '未能唤醒相关灵感。' });
                } else {
                    inspirationMessages.value.push({ role: 'assistant', type: 'results', results: results });
                }
            } catch (err) {
                inspirationMessages.value.push({ role: 'assistant', content: `错误: ${err.message}` });
            } finally {
                inspirationLoading.value = false;
                await scrollToBottom();
            }
        };

        const viewInspiration = (ins) => { viewingInspiration.value = ins; };
        const closeInspirationView = () => { viewingInspiration.value = null; };
        
        const confirmDeleteInspiration = async () => {
            if (!confirm('确定要删除这段灵感吗？此操作不可撤销。')) return;
            try {
                const res = await fetch(`/api/inspiration/delete/${viewingInspiration.value.id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error('删除失败');
                viewingInspiration.value = null;
                inspirationMessages.value.push({ role: 'assistant', content: '✅ 灵感已从库中移除。' });
            } catch (err) { alert(err.message); }
        };

        const handleSearch = async () => {
            const text = input.value.trim();
            if (!text || loading.value) return;

            // 添加用户消息
            messages.value.push({ role: 'user', content: text });
            input.value = '';
            loading.value = true;
            await scrollToBottom();

            try {
                await searchNotes(text);
            } catch (err) {
                messages.value.push({ 
                    role: 'assistant', 
                    content: `错误: ${err.message || '服务连接失败，请检查后端是否运行。'}` 
                });
            } finally {
                loading.value = false;
                await scrollToBottom();
            }
        };

        const searchNotes = async (query) => {
            const res = await fetch('/api/note/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, top_k: 3 })
            });
            
            if (!res.ok) {
                throw new Error('搜索请求失败');
            }
            
            const results = await res.json();
            
            if (results.length === 0) {
                messages.value.push({ 
                    role: 'assistant', 
                    content: '未找到相关笔记，请尝试其他关键词。' 
                });
            } else {
                messages.value.push({ 
                    role: 'assistant', 
                    type: 'results',
                    results: results 
                });
            }
        };

        // 添加笔记功能
        const openAddModal = () => {
            addingNote.value = true;
            addForm.value = {
                user_description: '',
                content: ''
            };
        };
        
        const cancelAdd = () => {
            if (addForm.value.content.trim() && !confirm('确定要关闭吗？未保存的内容将丢失。')) {
                return;
            }
            addingNote.value = false;
            addForm.value = {
                user_description: '',
                content: ''
            };
        };
        
        const saveAdd = async () => {
            if (!addForm.value.content.trim()) return;
            
            saving.value = true;
            
            try {
                const res = await fetch('/api/note/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        content: addForm.value.content,
                        description: addForm.value.user_description || null
                    })
                });
                
                if (!res.ok) {
                    throw new Error('保存笔记失败');
                }
                
                const data = await res.json();
                
                // 构建提示信息
                let statusMsg = `✅ 笔记已安全存入知识库 (ID: ${data.id})`;
                if (data.user_description) {
                    statusMsg += `\n📝 用户描述: ${data.user_description}`;
                }
                if (data.ai_description && data.ai_description !== data.user_description) {
                    statusMsg += `\n🤖 AI描述: ${data.ai_description}`;
                }
                
                messages.value.push({ 
                    role: 'assistant', 
                    type: 'status',
                    content: statusMsg.trim()
                });
                
                // 关闭模态框
                addingNote.value = false;
                addForm.value = {
                    user_description: '',
                    content: ''
                };
                
                // 滚动到底部
                await scrollToBottom();
            } catch (err) {
                messages.value.push({
                    role: 'assistant',
                    content: `❌ 保存失败: ${err.message}`
                });
            } finally {
                saving.value = false;
            }
        };
        
        // 查看功能
        const viewNote = (note) => {
            viewingNote.value = note;
        };
        
        const closeView = () => {
            viewingNote.value = null;
        };
        
        const switchToEdit = () => {
            if (viewingNote.value) {
                editingNote.value = viewingNote.value;
                editForm.value = {
                    user_description: viewingNote.value.user_description || '',
                    content: viewingNote.value.content || ''
                };
                viewingNote.value = null;
            }
        };
        
        // 编辑功能
        const startEdit = (note) => {
            editingNote.value = note;
            editForm.value = {
                user_description: note.user_description || '',
                content: note.content || ''
            };
        };
        
        const cancelEdit = () => {
            if (!confirm('确定要关闭编辑吗？未保存的更改将丢失。')) {
                return;
            }
            editingNote.value = null;
            editForm.value = {
                user_description: '',
                content: ''
            };
        };
        
        const saveEdit = async () => {
            if (!editForm.value.content.trim()) return;
            
            saving.value = true;
            
            try {
                const res = await fetch(`/api/note/update/${editingNote.value.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: editForm.value.content,
                        description: editForm.value.user_description || null
                    })
                });
                
                if (!res.ok) {
                    throw new Error('更新失败');
                }
                
                const data = await res.json();
                
                // 显示成功消息
                let statusMsg = `✅ 笔记已更新 (ID: ${data.id})`;
                if (data.ai_description) {
                    statusMsg += `\n🤖 新AI描述: ${data.ai_description}`;
                }
                
                messages.value.push({
                    role: 'assistant',
                    type: 'status',
                    content: statusMsg.trim()
                });
                
                // 关闭编辑框（不需要确认）
                editingNote.value = null;
                editForm.value = {
                    user_description: '',
                    content: ''
                };
                
                // 滚动到底部
                await scrollToBottom();
            } catch (err) {
                messages.value.push({
                    role: 'assistant',
                    content: `❌ 更新失败: ${err.message}`
                });
            } finally {
                saving.value = false;
            }
        };
        
        // 删除功能
        const confirmDelete = async () => {
            if (!confirm(`确定要删除这条笔记吗？\n\nID: ${editingNote.value.id}\n\n此操作不可恢复！`)) {
                return;
            }
            
            deleting.value = true;
            
            try {
                const res = await fetch(`/api/note/delete/${editingNote.value.id}`, {
                    method: 'DELETE'
                });
                
                if (!res.ok) {
                    throw new Error('删除失败');
                }
                
                messages.value.push({
                    role: 'assistant',
                    type: 'status',
                    content: `✅ 笔记已删除 (ID: ${editingNote.value.id})`
                });
                
                // 关闭编辑框（不需要确认）
                editingNote.value = null;
                editForm.value = {
                    user_description: '',
                    content: ''
                };
                
                // 滚动到底部
                await scrollToBottom();
            } catch (err) {
                messages.value.push({
                    role: 'assistant',
                    content: `❌ 删除失败: ${err.message}`
                });
            } finally {
                deleting.value = false;
            }
        };

        return {
            currentTab,
            input, loading, messages, messageBox, textarea,
            handleSearch,
            addingNote, addForm, openAddModal, cancelAdd, saveAdd,
            viewingNote, viewNote, closeView, switchToEdit,
            editingNote, editForm, saving, deleting,
            startEdit, cancelEdit, saveEdit, confirmDelete,
            // 灵感模块
            inspirationInput, inspirationLoading, inspirationMessages, inspirationMessageBox,
            addingInspiration, inspirationForm, inspirationSaving, viewingInspiration,
            openInspirationModal, cancelInspiration, saveInspiration, handleInspirationSearch,
            viewInspiration, closeInspirationView, confirmDeleteInspiration
        };
    }
}).mount('#app');

