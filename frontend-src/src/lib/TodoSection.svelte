<script>
  import { onMount } from 'svelte';
  import axios from 'axios';
  import { 
    CheckCircle2, Circle, Trash2, Sparkles, Plus, Send, 
    Clock, AlertCircle, Calendar, Coffee, ListTodo, X, ChevronDown, ChevronRight, Edit
  } from 'lucide-svelte';

  let todos = $state([]);
  let input = $state('');
  let loading = $state(false);
  let listLoading = $state(true);
  let filterMode = $state('pending'); // pending, completed
  let expandedTodos = $state(new Set()); // Track which todos are expanded

  // Date selection for completion
  let pendingTodoToComplete = $state(null);
  let completionDate = $state(new Date().toISOString().split('T')[0]);

  // AI Reviewing state
  let reviewingItems = $state(null);
  let parsing = $state(false);

  // Long press & Action Modal state
  let actionTodo = $state(null);
  let pressTimer;
  let isLongPress = false;

  // Edit modal state
  let editingTodo = $state(null);
  let editForm = $state({ task: '', priority: '' });

  function handlePressStart(todo) {
    isLongPress = false;
    pressTimer = setTimeout(() => {
      isLongPress = true;
      actionTodo = todo;
      if (window.navigator.vibrate) window.navigator.vibrate(50); // 震动反馈
    }, 600); // 600ms 定义为长按
  }

  function handlePressEnd() {
    clearTimeout(pressTimer);
  }

  function openEdit(todo) {
    editingTodo = todo;
    editForm = { task: todo.task, priority: todo.priority };
    actionTodo = null;
  }

  async function saveEdit() {
    if (!editForm.task.trim()) return;
    try {
      // 复用之前的更新逻辑，但在 service 增加具体任务修改支持
      await axios.put(`/api/todo/update_info/${editingTodo.id}`, editForm);
      editingTodo.task = editForm.task;
      editingTodo.priority = editForm.priority;
      editingTodo = null;
    } catch (err) {
      alert('更新失败: ' + err.message);
    }
  }

  async function resetTodo(todo) {
    try {
      await axios.put(`/api/todo/update/${todo.id}`, { status: 'pending' });
      todo.status = 'pending';
      todo.completed_at = null;
      // 同时重置所有子任务
      if (todo.subtasks) {
        todo.subtasks.forEach(st => {
          st.status = 'pending';
          st.completed_at = null;
        });
      }
      actionTodo = null;
    } catch (err) {
      alert('重置失败: ' + err.message);
    }
  }

  let showAddModal = $state(false);
  const slogans = [
    "✨ 今天又是充满活力的一天！加油！",
    "🚀 把大任务拆解，每一步都是进步。",
    "💡 专注当下，你的努力终将开花结果。",
    "🌿 不要为明天忧虑，先做好今天的事。",
    "🎯 记录灵感，捕获每一瞬间的可能。"
  ];
  let randomSlogan = $state(slogans[0]);

  onMount(async () => {
    randomSlogan = slogans[Math.floor(Math.random() * slogans.length)];
    await fetchTodos();
  });

  async function fetchTodos() {
    listLoading = true;
    try {
      const res = await axios.get('/api/todo/list');
      todos = res.data;
    } catch (err) {
      console.error('获取待办失败:', err);
    } finally {
      listLoading = false;
    }
  }

  async function handleAIParse() {
    if (!input.trim() || parsing) return;
    parsing = true;
    try {
      const res = await axios.post('/api/todo/parse', { content: input }, { timeout: 15000 });
      reviewingItems = res.data.map(item => ({
        ...item,
        id: Math.random().toString(36).substr(2, 9),
        subtasks: (item.subtasks || []).map(st => ({
          ...st,
          id: Math.random().toString(36).substr(2, 9)
        }))
      }));
      showAddModal = false; // Close add modal after successful parse
    } catch (err) {
      console.warn('AI解析失败或超时，切换为普通模式:', err);
      // Fallback: Use default method to add todo if AI fails
      reviewingItems = [{
        id: Math.random().toString(36).substr(2, 9),
        task: input,
        priority: '近期',
        subtasks: [],
        reminder_at: null
      }];
      showAddModal = false;
    } finally {
      parsing = false;
    }
  }

  async function confirmAndSave() {
    if (!reviewingItems || reviewingItems.length === 0) return;
    loading = true;
    try {
      await axios.post('/api/todo/add', { items: reviewingItems });
      input = '';
      reviewingItems = null;
      await fetchTodos();
    } catch (err) {
      alert('保存失败: ' + err.message);
    } finally {
      loading = false;
    }
  }

  function toggleExpand(todoId) {
    if (expandedTodos.has(todoId)) {
      expandedTodos.delete(todoId);
    } else {
      expandedTodos.add(todoId);
    }
    expandedTodos = new Set(expandedTodos); // Trigger reactivity
  }

  async function toggleStatus(todo) {
    // If has subtasks, toggle expand instead of completing
    if (todo.subtasks && todo.subtasks.length > 0) {
      toggleExpand(todo.id);
      return;
    }

    // Original toggle behavior for tasks without subtasks
    if (todo.status === 'pending') {
      // Show date picker modal before completing
      pendingTodoToComplete = todo;
      completionDate = new Date().toISOString().split('T')[0];
      return;
    }

    // Reverting to pending
    const newStatus = 'pending';
    try {
      await axios.put(`/api/todo/update/${todo.id}`, { status: newStatus });
      todo.status = newStatus;
      todo.completed_at = null;
    } catch (err) {
      alert('更新失败: ' + err.message);
    }
  }

  async function toggleSubtaskStatus(todo, subtask) {
    const newStatus = subtask.status === 'pending' ? 'completed' : 'pending';
    const completed_at = newStatus === 'completed' ? new Date().toISOString().split('T')[0] : null;
    
    try {
      await axios.put(`/api/todo/update/${todo.id}/subtask`, { 
        subtask_id: subtask.id,
        status: newStatus,
        completed_at 
      });
      subtask.status = newStatus;
      subtask.completed_at = completed_at;
      
      // Check if all subtasks are completed
      const allCompleted = todo.subtasks.every(st => st.status === 'completed');
      if (allCompleted) {
        todo.status = 'completed';
        todo.completed_at = new Date().toISOString().split('T')[0];
      }else{
        todo.status = 'pending';
        todo.completed_at = null;
      }
    } catch (err) {
      alert('更新失败: ' + err.message);
    }
  }

  async function confirmCompletion() {
    if (!pendingTodoToComplete) return;
    
    const todo = pendingTodoToComplete;
    const newStatus = 'completed';
    try {
      await axios.put(`/api/todo/update/${todo.id}`, { 
        status: newStatus,
        completed_at: completionDate 
      });
      todo.status = newStatus;
      todo.completed_at = completionDate;
      pendingTodoToComplete = null;
    } catch (err) {
      alert('更新失败: ' + err.message);
    }
  }

  async function deleteTodo(id) {
    if (!confirm('确定删除吗？')) return;
    try {
      await axios.delete(`/api/todo/delete/${id}`);
      todos = todos.filter(t => t.id !== id);
    } catch (err) {
      alert('删除失败: ' + err.message);
    }
  }

  function getDuration(todo) {
    if (!todo.completed_at || !todo.created_at) return '';
    const start = new Date(todo.created_at.split('T')[0]).getTime();
    const end = new Date(todo.completed_at).getTime();
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '当天完成';
    return `耗时 ${diffDays} 天`;
  }

  function getElapsedTime(createdAt) {
    if (!createdAt) return '';
    const start = new Date(createdAt.split('T')[0]).getTime();
    const now = new Date().getTime();
    const diffTime = now - start;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '今天创建';
    return `已过去 ${diffDays} 天`;
  }

  function getRemainingTime(reminderAt) {
    if (!reminderAt) return null;
    const now = new Date();
    const reminder = new Date(reminderAt);
    const diff = reminder.getTime() - now.getTime();
    
    if (diff < 0) return '已超时';
    
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    
    if (days > 0) return `剩余 ${days} 天 ${hours} 小时`;
    if (hours > 0) return `剩余 ${hours} 小时`;
    return '即将到期';
  }

  function getPriorityColor(p) {
    switch (p) {
      case '紧急': return 'text-red-500 bg-red-50 border-red-100';
      case '近期': return 'text-orange-500 bg-orange-50 border-orange-100';
      case '长期': return 'text-blue-500 bg-blue-50 border-blue-100';
      default: return 'text-slate-500 bg-slate-50 border-slate-100';
    }
  }

  function getPriorityIcon(p) {
    switch (p) {
      case '紧急': return AlertCircle;
      case '近期': return Clock;
      case '长期': return Calendar;
      default: return Coffee;
    }
  }
</script>

<div class="flex-1 flex flex-col overflow-hidden bg-white md:rounded-2xl shadow-sm border border-slate-200">
  <!-- Header / Slogan Area -->
  <div class="p-6 border-b border-slate-100 bg-gradient-to-r from-blue-50/50 to-indigo-50/50">
    <div class="max-w-3xl mx-auto flex justify-between items-center">
      <div class="flex flex-col gap-1">
        <h2 class="text-lg font-bold text-slate-800 tracking-tight">我的任务</h2>
        <p class="text-xs text-slate-500 font-medium">{randomSlogan}</p>
      </div>
      <button 
        onclick={() => showAddModal = true}
        class="bg-blue-600 text-white px-5 py-2.5 rounded-xl hover:bg-blue-700 transition flex items-center gap-2 text-sm font-bold shadow-lg shadow-blue-100 active:scale-95"
      >
        <Plus size={18} />
        <span>添加待办</span>
      </button>
    </div>
  </div>

  <!-- Add Todo Modal -->
  {#if showAddModal}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
      <div class="bg-white rounded-3xl shadow-2xl w-full max-w-xl overflow-hidden animate-in zoom-in-95 flex flex-col">
        <div class="p-6 border-b border-slate-100 bg-blue-50/50 flex justify-between items-center">
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-100">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-800">AI 智能任务拆解</h3>
              <p class="text-xs text-slate-500">输入一段话，让 AI 帮您规划任务步骤</p>
            </div>
          </div>
          <button onclick={() => showAddModal = false} class="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={24} />
          </button>
        </div>
        
        <div class="p-6 space-y-4">
          <div class="relative">
            <textarea 
              bind:value={input}
              placeholder="输入您的自然语言描述，例如：'明天上午要开会，下午记得去健身房，还有下周要把项目报告写完...'"
              class="w-full bg-slate-50 border-2 border-slate-100 focus:border-blue-200 rounded-2xl px-5 py-4 outline-none transition-all text-sm md:text-base resize-none shadow-inner"
              rows="5"
            ></textarea>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button 
              onclick={() => showAddModal = false}
              class="flex-1 px-4 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-all"
            >
              取消
            </button>
            <button 
              onclick={handleAIParse}
              disabled={!input.trim() || parsing}
              class="flex-[2] bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 transition flex items-center justify-center gap-2 text-sm font-bold shadow-lg shadow-blue-100"
            >
              {#if parsing}
                <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>解析中...</span>
              {:else}
                <Sparkles size={18} />
                <span>开始智能拆解</span>
              {/if}
            </button>
          </div>
        </div>
      </div>
    </div>
  {/if}

  <!-- AI Review Modal -->
  {#if reviewingItems}
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
      <div class="bg-white rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in zoom-in-95 flex flex-col max-h-[90vh]">
        <div class="p-6 border-b border-slate-100 bg-blue-50/50 flex justify-between items-center flex-shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-100">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-800">核对 AI 拆解任务</h3>
              <p class="text-xs text-slate-500">您可以修改任务内容、优先级及设置提醒时间</p>
            </div>
          </div>
          <button onclick={() => reviewingItems = null} class="text-slate-400 hover:text-slate-600 transition-colors">
            <X size={24} />
          </button>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/30">
          {#each reviewingItems as item (item.id)}
            <div class="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm space-y-3">
              <div class="flex items-start gap-3">
                <textarea 
                  bind:value={item.task} 
                  rows="2"
                  class="flex-1 text-sm font-medium text-slate-700 outline-none bg-slate-50 border-2 border-transparent focus:border-blue-100 rounded-xl px-3 py-2 transition-all resize-none"
                ></textarea>
                <div class="flex flex-col gap-2">
                  <select 
                    bind:value={item.priority}
                    class="text-xs font-bold px-3 py-2 rounded-xl bg-slate-100 border-none outline-none cursor-pointer hover:bg-slate-200 transition-colors"
                  >
                    <option value="紧急">紧急</option>
                    <option value="近期">近期</option>
                    <option value="长期">长期</option>
                    <option value="待定">待定</option>
                  </select>
                  <button 
                    onclick={() => reviewingItems = reviewingItems.filter(i => i.id !== item.id)}
                    class="p-2 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all self-end"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              
              <!-- Subtasks Section -->
              {#if item.subtasks && item.subtasks.length > 0}
                <div class="pl-4 border-l-2 border-blue-100 space-y-2">
                  <div class="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <ListTodo size={10} />
                    子步骤 ({item.subtasks.length})
                  </div>
                  {#each item.subtasks as subtask, idx (subtask.id)}
                    <div class="flex items-center gap-2 group">
                      <span class="text-[10px] text-slate-400 font-mono w-5">{idx + 1}.</span>
                      <input 
                        bind:value={subtask.task}
                        class="flex-1 text-xs bg-slate-50 border border-slate-100 focus:border-blue-100 rounded-lg px-2 py-1.5 outline-none transition-all"
                      />
                      <button 
                        onclick={() => item.subtasks = item.subtasks.filter(st => st.id !== subtask.id)}
                        class="opacity-0 group-hover:opacity-100 p-1 text-slate-300 hover:text-red-400 rounded transition-all"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  {/each}
                  <button 
                    onclick={() => item.subtasks = [...item.subtasks, { id: Math.random().toString(36).substr(2, 9), task: '' }]}
                    class="text-[10px] text-blue-500 hover:text-blue-600 font-medium flex items-center gap-1 mt-1"
                  >
                    <Plus size={10} />
                    添加子步骤
                  </button>
                </div>
              {:else}
                <button 
                  onclick={() => item.subtasks = [{ id: Math.random().toString(36).substr(2, 9), task: '' }]}
                  class="text-xs text-slate-400 hover:text-blue-500 font-medium flex items-center gap-1 transition-colors"
                >
                  <Plus size={12} />
                  添加子步骤
                </button>
              {/if}
              
              <div class="flex items-center gap-3 pt-2 border-t border-slate-50">
                <div class="flex items-center gap-2 text-slate-400">
                  <Clock size={14} />
                  <span class="text-[11px] font-bold uppercase tracking-wider">提醒时间 (可选)</span>
                </div>
                <input 
                  type="datetime-local" 
                  bind:value={item.reminder_at}
                  class="text-xs bg-slate-50 border border-slate-100 rounded-lg px-2 py-1 outline-none focus:border-blue-200 text-slate-600"
                />
              </div>
            </div>
          {/each}
          
          {#if reviewingItems.length === 0}
            <div class="text-center py-10 text-slate-400">
              <p>任务已被清空</p>
            </div>
          {/if}
        </div>

        <div class="p-6 border-t border-slate-100 bg-white flex gap-3 flex-shrink-0">
          <button 
            onclick={() => reviewingItems = null}
            class="flex-1 px-6 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-2xl transition-all"
          >
            取消
          </button>
          <button 
            onclick={confirmAndSave}
            disabled={reviewingItems.length === 0 || loading}
            class="flex-[2] px-8 py-3 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:opacity-50 transition-all shadow-lg shadow-blue-100 flex items-center justify-center gap-2"
          >
            {#if loading}
              <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>保存中...</span>
            {:else}
              <Plus size={18} />
              <span>确认加入待办列表</span>
            {/if}
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Filter & Controls -->
  <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-white">
    <div class="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
      <button 
        onclick={() => filterMode = 'pending'}
        class="px-5 py-1.5 text-xs font-bold rounded-lg transition-all {filterMode === 'pending' ? 'bg-white text-blue-600 shadow-sm translate-y-[-1px]' : 'text-slate-500 hover:text-slate-700'}"
      >
        进行中
      </button>
      <button 
        onclick={() => filterMode = 'completed'}
        class="px-5 py-1.5 text-xs font-bold rounded-lg transition-all {filterMode === 'completed' ? 'bg-white text-green-600 shadow-sm translate-y-[-1px]' : 'text-slate-500 hover:text-slate-700'}"
      >
        已完成
      </button>
    </div>
    <div class="text-[10px] text-slate-400 font-medium uppercase tracking-wider">
      {filterMode === 'pending' ? '待处理' : '已归档'}: {todos.filter(t => t.status === filterMode).length}
    </div>
  </div>

  <!-- Task List Area -->
  <div class="flex-1 overflow-y-auto p-6 bg-white">
    <div class="max-w-3xl mx-auto">
      {#if listLoading}
        <div class="flex flex-col items-center justify-center py-12">
          <div class="w-10 h-10 border-4 border-slate-100 border-t-blue-500 rounded-full animate-spin"></div>
        </div>
      {:else if todos.filter(t => t.status === filterMode).length === 0}
        <div class="flex flex-col items-center justify-center py-20 text-slate-400 space-y-4">
          <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center">
            <ListTodo size={32} class="opacity-20" />
          </div>
          <p class="text-sm">
            {filterMode === 'pending' ? '太棒了，目前没有待处理的任务' : '还没有已完成的任务，继续加油'}
          </p>
        </div>
      {:else}
        <div class="space-y-4">
          {#each todos.filter(t => t.status === filterMode) as todo (todo.id)}
            <div class="animate-in fade-in slide-in-from-bottom-2">
              {@render TodoItemComponent({todo, toggleStatus, deleteTodo, getPriorityIcon, getPriorityColor, getDuration, getRemainingTime, getElapsedTime, toggleSubtaskStatus, expandedTodos})}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Completion Date Modal -->
{#if pendingTodoToComplete}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
  <div class="bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95">
    <div class="p-6 text-center border-b border-slate-100 bg-slate-50/50">
      <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <CheckCircle2 size={32} class="text-green-600" />
      </div>
      <h3 class="text-lg font-bold text-slate-800">标记为已完成</h3>
      <p class="text-sm text-slate-500 mt-1 px-4">“{pendingTodoToComplete.task}”</p>
    </div>
    <div class="p-6 space-y-4">
      <div>
        <label for="completion-date" class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">完成日期</label>
        <input 
          id="completion-date"
          type="date" 
          bind:value={completionDate}
          class="w-full bg-slate-50 border-2 border-slate-100 focus:border-blue-200 rounded-xl px-4 py-3 outline-none transition-all font-medium text-slate-700"
        />
      </div>
      <div class="flex gap-3 pt-2">
        <button 
          onclick={() => pendingTodoToComplete = null}
          class="flex-1 px-4 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-all"
        >
          取消
        </button>
        <button 
          onclick={confirmCompletion}
          class="flex-1 px-4 py-3 bg-blue-600 text-white font-bold hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-100 transition-all"
        >
          确定完成
        </button>
      </div>
    </div>
  </div>
</div>
{/if}

<!-- Action Menu Modal -->
{#if actionTodo}
<div class="fixed inset-0 z-50 flex items-end justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
  <div class="bg-white rounded-t-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in slide-in-from-bottom">
    <div class="p-6 border-b border-slate-100">
      <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest text-center">操作任务</h3>
      <p class="text-slate-700 font-medium text-center mt-2 line-clamp-1">“{actionTodo.task}”</p>
    </div>
    <div class="p-4 grid grid-cols-1 gap-2">
      <button 
        onclick={() => openEdit(actionTodo)}
        class="flex items-center justify-center gap-3 w-full p-4 hover:bg-slate-50 text-blue-600 font-bold rounded-2xl transition-all"
      >
        <Edit size={20} />
        <span>编辑任务</span>
      </button>
      <button 
        onclick={() => resetTodo(actionTodo)}
        class="flex items-center justify-center gap-3 w-full p-4 hover:bg-slate-50 text-orange-600 font-bold rounded-2xl transition-all"
      >
        <Clock size={20} />
        <span>重置/还原状态</span>
      </button>
      <button 
        onclick={() => { deleteTodo(actionTodo.id); actionTodo = null; }}
        class="flex items-center justify-center gap-3 w-full p-4 hover:bg-red-50 text-red-600 font-bold rounded-2xl transition-all"
      >
        <Trash2 size={20} />
        <span>删除任务</span>
      </button>
      <div class="h-px bg-slate-100 my-2"></div>
      <button 
        onclick={() => actionTodo = null}
        class="w-full p-4 text-slate-500 font-bold hover:bg-slate-100 rounded-2xl transition-all"
      >
        取消
      </button>
    </div>
  </div>
</div>
{/if}

<!-- Edit Modal -->
{#if editingTodo}
<div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in">
  <div class="bg-white rounded-3xl shadow-2xl w-full max-w-sm overflow-hidden animate-in zoom-in-95">
    <div class="p-6 border-b border-slate-100">
      <h3 class="text-lg font-bold text-slate-800">编辑任务</h3>
    </div>
    <div class="p-6 space-y-4">
      <div>
        <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">任务名称</label>
        <textarea 
          bind:value={editForm.task}
          class="w-full bg-slate-50 border-2 border-slate-100 focus:border-blue-200 rounded-xl px-4 py-3 outline-none transition-all text-sm resize-none"
          rows="3"
        ></textarea>
      </div>
      <div>
        <label class="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">优先级</label>
        <select 
          bind:value={editForm.priority}
          class="w-full bg-slate-50 border-2 border-slate-100 focus:border-blue-200 rounded-xl px-4 py-3 outline-none transition-all text-sm font-bold"
        >
          <option value="紧急">紧急</option>
          <option value="近期">近期</option>
          <option value="长期">长期</option>
          <option value="待定">待定</option>
        </select>
      </div>
      <div class="flex gap-3 pt-2">
        <button 
          onclick={() => editingTodo = null}
          class="flex-1 px-4 py-3 text-slate-500 font-bold hover:bg-slate-100 rounded-xl transition-all"
        >
          取消
        </button>
        <button 
          onclick={saveEdit}
          class="flex-1 px-4 py-3 bg-blue-600 text-white font-bold hover:bg-blue-700 rounded-xl shadow-lg shadow-blue-100 transition-all"
        >
          保存修改
        </button>
      </div>
    </div>
  </div>
</div>
{/if}

<!-- Internal Component for Todo Item -->
{#snippet TodoItemComponent({todo, toggleStatus, deleteTodo, getPriorityIcon, getPriorityColor, getDuration, getRemainingTime, toggleSubtaskStatus, expandedTodos})}
  {@const Icon = getPriorityIcon(todo.priority)}
  {@const hasSubtasks = todo.subtasks && todo.subtasks.length > 0}
  {@const isExpanded = expandedTodos.has(todo.id)}
  {@const completedSubtasks = hasSubtasks ? todo.subtasks.filter(st => st.status === 'completed').length : 0}
  
  <div 
    onmousedown={() => handlePressStart(todo)}
    onmouseup={handlePressEnd}
    onmouseleave={handlePressEnd}
    ontouchstart={() => handlePressStart(todo)}
    ontouchend={handlePressEnd}
    class="group rounded-2xl border border-slate-100 hover:border-blue-100 hover:shadow-sm transition-all {todo.status === 'completed' ? 'bg-slate-50/50 border-dashed opacity-80' : 'bg-white'}"
  >
    <!-- Main Task -->
    <div class="flex items-center gap-4 p-4">
      <button 
        onclick={() => toggleStatus(todo)} 
        class="transition-transform active:scale-90 flex-shrink-0"
      >
        {#if todo.status === 'completed'}
          <CheckCircle2 size={24} class="text-green-500" />
        {:else if hasSubtasks}
          {#if isExpanded}
            <ChevronDown size={24} class="text-blue-400" />
          {:else}
            <ChevronRight size={24} class="text-slate-300 group-hover:text-blue-400" />
          {/if}
        {:else}
          <Circle size={24} class="text-slate-300 group-hover:text-blue-400" />
        {/if}
      </button>
      
      <div class="flex-1 min-w-0">
        <div class="text-sm md:text-base font-medium transition-all {todo.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-700'}">
          {todo.task}
        </div>
        <div class="flex flex-wrap items-center gap-2 mt-1.5">
          <div class="flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold {getPriorityColor(todo.priority)}">
            <Icon size={10} />
            {todo.priority}
          </div>

          <!-- 步骤进度优化 -->
          {#if hasSubtasks}
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 {todo.status === 'completed' ? 'bg-slate-100 text-slate-500' : 'bg-blue-50 text-blue-600'}">
              <ListTodo size={10} />
              {#if todo.status === 'completed'}
                共 {todo.subtasks.length} 步已完成
              {:else}
                还剩 {todo.subtasks.length - completedSubtasks} / 共 {todo.subtasks.length} 步
              {/if}
            </span>
          {/if}

          <!-- 时间显示优化 -->
          {#if todo.status === 'completed'}
            <span class="text-[10px] text-green-600 font-bold bg-green-50 px-1.5 py-0.5 rounded flex items-center gap-1">
              <CheckCircle2 size={10} />
              {getDuration(todo)}
            </span>
          {:else}
            <span class="text-[10px] text-slate-400 font-medium bg-slate-100 px-1.5 py-0.5 rounded flex items-center gap-1">
              <Clock size={10} />
              {getElapsedTime(todo.created_at)}
            </span>
          {/if}

          {#if todo.status === 'pending' && todo.reminder_at}
            <span class="text-[10px] text-blue-600 font-bold bg-blue-50 px-1.5 py-0.5 rounded flex items-center gap-1 border border-blue-100">
              <Calendar size={10} />
              {getRemainingTime(todo.reminder_at)}
            </span>
          {/if}
        </div>
      </div>

      <button 
        onclick={() => deleteTodo(todo.id)}
        class="opacity-0 group-hover:opacity-100 p-2 text-slate-300 hover:text-red-400 hover:bg-red-50 rounded-lg transition-all flex-shrink-0"
      >
        <Trash2 size={18} />
      </button>
    </div>

    <!-- Subtasks (Expanded) -->
    {#if hasSubtasks && isExpanded}
      <div class="px-4 pb-4 border-t border-slate-100/50">
        <div class="pl-10 space-y-2 mt-3">
          {#each todo.subtasks as subtask, idx (subtask.id)}
            <div class="flex items-center gap-3 group/subtask py-1.5">
              <button 
                onclick={() => toggleSubtaskStatus(todo, subtask)}
                class="transition-transform active:scale-90 flex-shrink-0"
              >
                {#if subtask.status === 'completed'}
                  <CheckCircle2 size={18} class="text-green-500" />
                {:else}
                  <Circle size={18} class="text-slate-300 group-hover/subtask:text-blue-400" />
                {/if}
              </button>
              <span class="text-[11px] text-slate-400 font-mono w-4">{idx + 1}.</span>
              <span class="flex-1 text-sm {subtask.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-600'}">
                {subtask.task}
              </span>
              {#if subtask.status === 'completed' && subtask.completed_at}
                <span class="text-[9px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded">
                  ✓ {new Date(subtask.completed_at).toLocaleDateString()}
                </span>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  </div>
{/snippet}

