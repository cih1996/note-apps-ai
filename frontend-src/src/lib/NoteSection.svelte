<script>
  import { onMount, tick } from 'svelte';
  import axios from 'axios';
  import { Search, Plus, Send, Edit, ExternalLink, CheckCircle2, Tag, X } from 'lucide-svelte';

  let messages = $state([]);
  let input = $state('');
  let loading = $state(false);
  let messageBox = $state(null);

  // Tags state
  let allTags = $state([]);
  let selectedFilterTags = $state([]);

  // Note creation modal state
  let addingNote = $state(false);
  let addForm = $state({ content: '', description: '', tags: [] });
  let newTagInput = $state('');
  let saving = $state(false);

  // Edit/View modal state
  let viewingNote = $state(null);
  let editingNote = $state(null);
  let editForm = $state({ content: '', description: '', tags: [] });
  let editTagInput = $state('');
  let deleting = $state(false);

  onMount(async () => {
    fetchTags();
  });

  async function fetchTags() {
    try {
      const res = await axios.get('/api/note/tags');
      allTags = res.data;
    } catch (err) {
      console.error('获取标签失败:', err);
    }
  }

  async function scrollToBottom() {
    await tick();
    if (messageBox) {
      messageBox.scrollTop = messageBox.scrollHeight;
    }
  }

  function toggleFilterTag(tag) {
    if (selectedFilterTags.includes(tag)) {
      selectedFilterTags = selectedFilterTags.filter(t => t !== tag);
    } else {
      selectedFilterTags = [...selectedFilterTags, tag];
    }
  }

  async function handleSearch() {
    const text = input.trim();
    if (!text && selectedFilterTags.length === 0) return;
    if (loading) return;

    messages.push({ role: 'user', content: text || '(按标签筛选)' });
    input = '';
    loading = true;
    await scrollToBottom();

    try {
      const res = await axios.post('/api/note/search', { 
        query: text, 
        top_k: 3,
        tags: selectedFilterTags.length > 0 ? selectedFilterTags : null
      });
      const results = res.data;

      if (results.length === 0) {
        messages.push({ role: 'assistant', content: '未找到相关笔记，请尝试其他关键词或调整标签筛选。' });
      } else {
        messages.push({ role: 'assistant', type: 'results', results });
      }
    } catch (err) {
      messages.push({ role: 'assistant', content: `错误: ${err.response?.data?.detail || err.message}` });
    } finally {
      loading = false;
      await scrollToBottom();
    }
  }

  function openAddModal() {
    addingNote = true;
    addForm = { content: '', description: '', tags: [] };
    newTagInput = '';
  }

  function addTagToForm(isEdit = false) {
    const tag = (isEdit ? editTagInput : newTagInput).trim();
    if (!tag) return;
    
    if (isEdit) {
      if (!editForm.tags.includes(tag)) {
        editForm.tags = [...editForm.tags, tag];
      }
      editTagInput = '';
    } else {
      if (!addForm.tags.includes(tag)) {
        addForm.tags = [...addForm.tags, tag];
      }
      newTagInput = '';
    }
  }

  function removeTagFromForm(tag, isEdit = false) {
    if (isEdit) {
      editForm.tags = editForm.tags.filter(t => t !== tag);
    } else {
      addForm.tags = addForm.tags.filter(t => t !== tag);
    }
  }

  async function saveAdd() {
    if (!addForm.content.trim() || saving) return;
    saving = true;
    try {
      const res = await axios.post('/api/note/add', {
        content: addForm.content,
        description: addForm.description || null,
        tags: addForm.tags
      });
      const data = res.data;

      let statusMsg = `✅ 笔记已存入知识库 (ID: ${data.id})`;
      
      // 如果 AI 描述存在且与用户原始描述不同，说明 AI 成功生成了内容
      if (data.ai_description && data.ai_description !== addForm.description) {
        statusMsg += `\n🤖 AI 智能概括: ${data.ai_description}`;
      } else if (addForm.description) {
        statusMsg += `\n📝 已同步您的描述`;
      }

      messages.push({ role: 'assistant', type: 'status', content: statusMsg });
      addingNote = false;
      fetchTags(); // 刷新标签列表
      await scrollToBottom();
    } catch (err) {
      alert('保存失败: ' + err.message);
    } finally {
      saving = false;
    }
  }

  function startEdit(note) {
    editingNote = note;
    editForm = { 
      content: note.content, 
      description: note.user_description || '',
      tags: [...(note.tags || [])]
    };
    editTagInput = '';
  }

  async function saveEdit() {
    if (!editForm.content.trim() || saving) return;
    saving = true;
    try {
      await axios.put(`/api/note/update/${editingNote.id}`, {
        content: editForm.content,
        description: editForm.description || null,
        tags: editForm.tags
      });
      messages.push({ role: 'assistant', type: 'status', content: `✅ 笔记已更新 (ID: ${editingNote.id})` });
      editingNote = null;
      fetchTags(); // 刷新标签列表
      await scrollToBottom();
    } catch (err) {
      alert('更新失败: ' + err.message);
    } finally {
      saving = false;
    }
  }

  async function confirmDelete() {
    if (!confirm('确定要删除这条笔记吗？') || deleting) return;
    deleting = true;
    try {
      await axios.delete(`/api/note/delete/${editingNote.id}`);
      messages.push({ role: 'assistant', type: 'status', content: `✅ 笔记已删除 (ID: ${editingNote.id})` });
      editingNote = null;
      await scrollToBottom();
    } catch (err) {
      alert('删除失败: ' + err.message);
    } finally {
      deleting = false;
    }
  }
</script>

<div class="flex-1 flex flex-col overflow-hidden bg-white md:rounded-2xl shadow-sm border border-slate-200">
  <!-- Messages Area -->
  <div bind:this={messageBox} class="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
    {#if messages.length === 0}
      <div class="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
        <Search size={48} class="opacity-20" />
        <p class="text-sm md:text-base">输入关键词搜索笔记</p>
        <div class="flex flex-wrap justify-center gap-2">
          <button onclick={() => { input = '如何安装Docker'; handleSearch(); }} class="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1 rounded-full transition">搜索 "Docker安装"</button>
          <button onclick={() => { input = '代码片段'; handleSearch(); }} class="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1 rounded-full transition">搜索 "代码片段"</button>
        </div>
      </div>
    {/if}

    {#each messages as msg}
      <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
        <div class="max-w-[85%] rounded-2xl p-4 shadow-sm {msg.role === 'user' ? 'bg-primary text-white rounded-tr-none' : 'bg-slate-100 text-slate-800 rounded-tl-none'}">
          {#if msg.type === 'status'}
            <div class="flex items-center gap-2 text-sm font-medium">
              <CheckCircle2 size={16} class="text-green-500" />
              <span class="whitespace-pre-wrap">{msg.content}</span>
            </div>
          {:else if msg.type === 'results'}
            <div class="space-y-3">
              <div class="text-[10px] text-slate-400 mb-1 uppercase tracking-wider">找到 {msg.results.length} 条相关结果</div>
              {#each msg.results as note}
                <div 
                  onclick={() => viewingNote = note}
                  class="bg-white border border-slate-200 rounded-xl p-3 hover:border-primary/50 hover:shadow-md transition-all cursor-pointer group"
                >
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-[10px] text-slate-400 font-mono">{note.id}</span>
                    <div class="flex items-center gap-2">
                      <span class="text-[10px] font-bold {note.similarity > 70 ? 'text-green-600' : 'text-yellow-600'}">{note.similarity}%</span>
                    </div>
                  </div>
                  <div class="text-sm font-bold text-slate-800 mb-1">{note.ai_description || '无标题'}</div>
                  {#if note.tags && note.tags.length > 0}
                    <div class="flex flex-wrap gap-1 mb-2">
                      {#each note.tags as tag}
                        <span class="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-md flex items-center gap-1">
                          <Tag size={8} />
                          {tag}
                        </span>
                      {/each}
                    </div>
                  {/if}
                  <div class="text-xs text-slate-500 line-clamp-2 italic">{note.content}</div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
          {/if}
        </div>
      </div>
    {/each}

    {#if loading}
      <div class="flex justify-start">
        <div class="bg-slate-100 rounded-2xl p-4 rounded-tl-none flex space-x-2">
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
          <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Input Area -->
  <div class="p-4 border-t border-slate-100 bg-white">
    <!-- Tag Filter -->
    {#if allTags.length > 0}
      <div class="flex flex-wrap gap-2 mb-3 max-h-24 overflow-y-auto custom-scrollbar">
        {#each allTags as tag}
          <button 
            onclick={() => toggleFilterTag(tag)}
            class="text-[10px] px-2.5 py-1 rounded-full transition-all flex items-center gap-1.5
              {selectedFilterTags.includes(tag) 
                ? 'bg-primary text-white shadow-sm ring-2 ring-primary/20' 
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}"
          >
            <Tag size={10} />
            {tag}
          </button>
        {/each}
        {#if selectedFilterTags.length > 0}
          <button 
            onclick={() => selectedFilterTags = []}
            class="text-[10px] px-2.5 py-1 rounded-full bg-red-50 text-red-500 hover:bg-red-100 transition-all flex items-center gap-1"
          >
            <X size={10} />
            清除筛选
          </button>
        {/if}
      </div>
    {/if}

    <div class="flex items-center space-x-3">
      <button 
        onclick={openAddModal}
        class="p-3 text-slate-400 hover:text-primary hover:bg-blue-50 rounded-2xl transition-all"
        title="添加笔记"
      >
        <Plus size={24} />
      </button>
      <input 
        bind:value={input}
        onkeydown={(e) => e.key === 'Enter' && handleSearch()}
        type="text"
        placeholder="搜索笔记或直接对话..."
        class="flex-1 bg-slate-50 border-2 border-slate-100 focus:border-primary/30 rounded-2xl px-5 py-3 outline-none transition-all"
      />
      <button 
        onclick={handleSearch}
        disabled={!input || loading}
        class="bg-primary text-white p-3.5 rounded-2xl hover:opacity-90 disabled:opacity-50 transition shadow-lg shadow-blue-100"
      >
        <Send size={20} />
      </button>
    </div>
  </div>
</div>

<!-- Modals -->
{#if addingNote}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
    <div class="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-blue-50/50">
        <h3 class="text-xl font-bold text-slate-800">记录新笔记</h3>
        <button onclick={() => addingNote = false} class="text-slate-400 hover:text-slate-600">
          <Plus size={24} class="rotate-45" />
        </button>
      </div>
      <div class="p-6 space-y-4 overflow-y-auto">
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">简单描述</label>
          <input bind:value={addForm.description} type="text" placeholder="用于快速索引的关键词或描述" class="w-full bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-3 outline-none focus:border-primary/30" />
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">笔记内容</label>
          <textarea bind:value={addForm.content} rows="10" placeholder="支持 Markdown 和多行文本..." class="w-full bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-3 outline-none focus:border-primary/30 resize-none font-mono text-sm"></textarea>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">分类标签</label>
          <div class="space-y-3">
            <div class="flex gap-2">
              <input 
                bind:value={newTagInput} 
                onkeydown={(e) => e.key === 'Enter' && addTagToForm(false)}
                type="text" 
                placeholder="输入标签按回车确认" 
                class="flex-1 bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-2 outline-none focus:border-primary/30 text-sm" 
              />
              <button 
                onclick={() => addTagToForm(false)}
                class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition text-sm"
              >添加</button>
            </div>
            
            {#if addForm.tags.length > 0}
              <div class="flex flex-wrap gap-2">
                {#each addForm.tags as tag}
                  <span class="bg-blue-50 text-blue-600 px-3 py-1 rounded-lg text-xs flex items-center gap-2 group">
                    <Tag size={12} />
                    {tag}
                    <button onclick={() => removeTagFromForm(tag, false)} class="hover:text-red-500">
                      <X size={12} />
                    </button>
                  </span>
                {/each}
              </div>
            {/if}

            {#if allTags.length > 0}
              <div class="pt-2">
                <p class="text-[10px] text-slate-400 mb-2 font-medium">常用标签:</p>
                <div class="flex flex-wrap gap-2">
                  {#each allTags as tag}
                    {#if !addForm.tags.includes(tag)}
                      <button 
                        onclick={() => { addForm.tags = [...addForm.tags, tag] }}
                        class="text-[10px] bg-slate-100 text-slate-500 px-2 py-1 rounded-md hover:bg-slate-200 transition"
                      >
                        + {tag}
                      </button>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
      <div class="p-6 border-t border-slate-100 flex justify-end gap-3 bg-slate-50/30">
        <button onclick={() => addingNote = false} class="px-6 py-2.5 text-slate-500 hover:bg-slate-200 rounded-xl transition">取消</button>
        <div class="flex flex-col items-end">
          <button onclick={saveAdd} disabled={!addForm.content.trim() || saving} class="px-8 py-2.5 bg-primary text-white rounded-xl font-bold hover:opacity-90 disabled:opacity-50 transition shadow-lg shadow-blue-100">
            {saving ? '保存中...' : '存入知识库'}
          </button>
          <span class="text-[9px] text-slate-400 mt-1 mr-1">AI 自动摘要已启用 (可选)</span>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if viewingNote}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
    <div class="bg-white rounded-3xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex justify-between items-center">
        <div class="flex items-center gap-3">
          <span class="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded font-mono uppercase">{viewingNote.id}</span>
          <h3 class="text-xl font-bold text-slate-800">{viewingNote.ai_description || '笔记详情'}</h3>
        </div>
        <button onclick={() => viewingNote = null} class="text-slate-400 hover:text-slate-600">
          <Plus size={24} class="rotate-45" />
        </button>
      </div>
      <div class="p-8 overflow-y-auto space-y-6">
        {#if viewingNote.user_description}
          <div class="bg-blue-50/50 p-4 rounded-xl border border-blue-100/50 italic text-slate-600 text-sm">
            "{viewingNote.user_description}"
          </div>
        {/if}
        
        {#if viewingNote.tags && viewingNote.tags.length > 0}
          <div class="flex flex-wrap gap-2">
            {#each viewingNote.tags as tag}
              <span class="bg-blue-50 text-blue-600 px-3 py-1 rounded-lg text-xs flex items-center gap-2">
                <Tag size={12} />
                {tag}
              </span>
            {/each}
          </div>
        {/if}

        <div class="bg-slate-50 p-6 rounded-2xl border border-slate-100 whitespace-pre-wrap text-slate-700 font-mono text-sm leading-relaxed">
          {viewingNote.content}
        </div>
      </div>
      <div class="p-6 border-t border-slate-100 flex justify-end gap-3 bg-slate-50/30">
        <button 
          onclick={() => { 
            const noteToEdit = viewingNote;
            viewingNote = null; 
            startEdit(noteToEdit); 
          }} 
          class="px-6 py-2.5 bg-white border border-slate-200 text-primary hover:bg-blue-50 rounded-xl font-bold transition flex items-center gap-2"
        >
          <Edit size={18} />
          编辑笔记
        </button>
        <button onclick={() => viewingNote = null} class="px-8 py-2.5 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-900 transition">关闭</button>
      </div>
    </div>
  </div>
{/if}

{#if editingNote}
  <div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-in fade-in">
    <div class="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-blue-50/50">
        <h3 class="text-xl font-bold text-slate-800">编辑笔记</h3>
        <button onclick={() => editingNote = null} class="text-slate-400 hover:text-slate-600">
          <Plus size={24} class="rotate-45" />
        </button>
      </div>
      <div class="p-6 space-y-4 overflow-y-auto">
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">描述</label>
          <input bind:value={editForm.description} type="text" class="w-full bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-3 outline-none focus:border-primary/30" />
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">内容</label>
          <textarea bind:value={editForm.content} rows="10" class="w-full bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-3 outline-none focus:border-primary/30 resize-none font-mono text-sm"></textarea>
        </div>
        <div>
          <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">分类标签</label>
          <div class="space-y-3">
            <div class="flex gap-2">
              <input 
                bind:value={editTagInput} 
                onkeydown={(e) => e.key === 'Enter' && addTagToForm(true)}
                type="text" 
                placeholder="输入标签按回车确认" 
                class="flex-1 bg-slate-50 border-2 border-slate-100 rounded-xl px-4 py-2 outline-none focus:border-primary/30 text-sm" 
              />
              <button 
                onclick={() => addTagToForm(true)}
                class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl transition text-sm"
              >添加</button>
            </div>
            
            {#if editForm.tags.length > 0}
              <div class="flex flex-wrap gap-2">
                {#each editForm.tags as tag}
                  <span class="bg-blue-50 text-blue-600 px-3 py-1 rounded-lg text-xs flex items-center gap-2 group">
                    <Tag size={12} />
                    {tag}
                    <button onclick={() => removeTagFromForm(tag, true)} class="hover:text-red-500">
                      <X size={12} />
                    </button>
                  </span>
                {/each}
              </div>
            {/if}

            {#if allTags.length > 0}
              <div class="pt-2">
                <p class="text-[10px] text-slate-400 mb-2 font-medium">常用标签:</p>
                <div class="flex flex-wrap gap-2">
                  {#each allTags as tag}
                    {#if !editForm.tags.includes(tag)}
                      <button 
                        onclick={() => { editForm.tags = [...editForm.tags, tag] }}
                        class="text-[10px] bg-slate-100 text-slate-500 px-2 py-1 rounded-md hover:bg-slate-200 transition"
                      >
                        + {tag}
                      </button>
                    {/if}
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>
      <div class="p-6 border-t border-slate-100 flex justify-between items-center bg-slate-50/30">
        <button onclick={confirmDelete} disabled={deleting} class="px-6 py-2.5 text-red-500 hover:bg-red-50 rounded-xl transition font-medium">
          {deleting ? '删除中...' : '删除笔记'}
        </button>
        <div class="flex gap-3">
          <button onclick={() => editingNote = null} class="px-6 py-2.5 text-slate-500 hover:bg-slate-200 rounded-xl transition">取消</button>
          <button onclick={saveEdit} disabled={!editForm.content.trim() || saving} class="px-8 py-2.5 bg-primary text-white rounded-xl font-bold hover:opacity-90 disabled:opacity-50 transition shadow-lg shadow-blue-100">
            {saving ? '更新中...' : '保存更改'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

