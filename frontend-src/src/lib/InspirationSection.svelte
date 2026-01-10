<script>
  import { onMount, tick } from 'svelte';
  import axios from 'axios';
  import { Search, PenLine, Sparkles, Trash2, X, ChevronRight, MessageSquareQuote } from 'lucide-svelte';

  let inspirations = $state([]);
  let searchResults = $state(null);
  let input = $state('');
  let loading = $state(false);
  let listLoading = $state(true);

  // Modal states
  let addingInspiration = $state(false);
  let inspirationForm = $state({ content: '' });
  let inspirationSaving = $state(false);
  let viewingInspiration = $state(null);

  let limit = 10;
  let offset = 0;
  let hasMore = $state(true);

  onMount(async () => {
    await fetchInspirations();
  });

  async function fetchInspirations(isLoadMore = false) {
    if (!isLoadMore) {
      listLoading = true;
      offset = 0;
      inspirations = [];
    }
    
    try {
      const res = await axios.get(`/api/inspiration/list?limit=${limit}&offset=${offset}`);
      const newItems = res.data;
      
      if (newItems.length < limit) {
        hasMore = false;
      }
      
      inspirations = [...inspirations, ...newItems];
      offset += limit;
    } catch (err) {
      console.error('获取灵感失败:', err);
    } finally {
      listLoading = false;
    }
  }

  function handleScroll(e) {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 100 && !listLoading && hasMore && !searchResults) {
      fetchInspirations(true);
    }
  }

  async function handleSearch() {
    const text = input.trim();
    if (!text) {
      searchResults = null;
      return;
    }

    loading = true;
    try {
      const res = await axios.post('/api/inspiration/search', { query: text, top_k: 10 });
      searchResults = res.data;
    } catch (err) {
      alert('搜索失败: ' + err.message);
    } finally {
      loading = false;
    }
  }

  function openAddModal() {
    addingInspiration = true;
    inspirationForm = { content: '' };
  }

  async function saveInspiration() {
    if (!inspirationForm.content.trim() || inspirationSaving) return;
    inspirationSaving = true;
    try {
      const res = await axios.post('/api/inspiration/add', { content: inspirationForm.content });
      // Add to the top of the list
      inspirations.unshift({
        ...res.data,
        content: inspirationForm.content,
        created_at: new Date().toISOString()
      });
      addingInspiration = false;
      // Show details immediately? 
      viewingInspiration = inspirations[0];
    } catch (err) {
      alert('保存失败: ' + err.message);
    } finally {
      inspirationSaving = false;
    }
  }

  async function confirmDelete(ins) {
    if (!confirm('确定要删除这段灵感吗？此操作不可撤销。')) return;
    try {
      await axios.delete(`/api/inspiration/delete/${ins.id}`);
      inspirations = inspirations.filter(i => i.id !== ins.id);
      if (searchResults) searchResults = searchResults.filter(i => i.id !== ins.id);
      if (viewingInspiration?.id === ins.id) viewingInspiration = null;
    } catch (err) {
      alert('删除失败: ' + err.message);
    }
  }
</script>

<div class="flex-1 flex flex-col overflow-hidden bg-white md:rounded-2xl shadow-sm border border-slate-200 inspiration-theme">
  <!-- Search Header -->
  <div class="p-4 md:p-6 border-b border-slate-100 bg-white/80 backdrop-blur-sm z-10">
    <div class="relative max-w-2xl mx-auto">
      <input 
        bind:value={input}
        onkeydown={(e) => e.key === 'Enter' && handleSearch()}
        oninput={() => input === '' && (searchResults = null)}
        type="text"
        placeholder="搜寻过往的灵感与自诉..."
        class="w-full bg-slate-50 border-2 border-slate-100 focus:border-purple-200 rounded-2xl px-12 py-3.5 outline-none transition-all text-sm md:text-base shadow-inner"
      />
      <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
      {#if input}
        <button onclick={() => { input = ''; searchResults = null; }} class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
          <X size={18} />
        </button>
      {/if}
    </div>
  </div>

  <!-- Content List Area -->
  <div onscroll={handleScroll} class="flex-1 overflow-y-auto p-4 md:p-8 bg-slate-50/30">
    {#if loading || (listLoading && offset === 0)}
      <div class="flex flex-col items-center justify-center h-full py-12">
        <div class="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
        <p class="mt-4 text-slate-400 text-sm">正在唤醒记忆...</p>
      </div>
    {:else if searchResults}
      <!-- Search Results View -->
      <div class="max-w-4xl mx-auto space-y-6">
        <div class="flex items-center gap-2 text-xs text-slate-400 px-2">
          <Sparkles size={14} class="text-purple-400" />
          <span>相关灵感匹配</span>
          <div class="flex-1 h-px bg-slate-200"></div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          {#each searchResults as ins}
            <div 
              onclick={() => viewingInspiration = ins}
              class="bg-white border border-slate-200 rounded-2xl p-5 hover:border-purple-400 transition-all cursor-pointer shadow-sm hover:shadow-md group relative overflow-hidden"
            >
              <div class="flex justify-between items-start mb-3">
                <div class="bg-purple-50 text-purple-600 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">
                  {ins.theme}
                </div>
                <div class="text-[10px] text-slate-400 font-mono italic">
                  {ins.similarity}% 匹配
                </div>
              </div>
              <h3 class="text-base font-bold text-slate-800 mb-2 group-hover:text-purple-600 transition-colors">{ins.title}</h3>
              <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">{ins.summary}</p>
              <div class="flex flex-wrap gap-2">
                {#each ins.tags as tag}
                  <span class="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">#{tag}</span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {:else if inspirations.length === 0}
      <!-- Empty State -->
      <div class="flex flex-col items-center justify-center h-full text-center max-w-sm mx-auto space-y-6">
        <div class="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center text-purple-600">
          <MessageSquareQuote size={40} />
        </div>
        <div>
          <h2 class="text-xl font-bold text-slate-800 mb-2">此处允许混乱</h2>
          <p class="text-sm text-slate-500 leading-relaxed italic">
            这里是您的私人精神角落。保留原始自我，尽管倾诉，AI 将为您提炼索引。
          </p>
        </div>
        <button onclick={openAddModal} class="px-8 py-3 bg-purple-600 text-white rounded-2xl font-bold shadow-lg shadow-purple-100 hover:bg-purple-700 transition flex items-center gap-2">
          <PenLine size={20} />
          记录第一段灵感
        </button>
      </div>
    {:else}
      <!-- Default List View (Recent) -->
      <div class="max-w-2xl mx-auto space-y-8 pb-24">
        {#each inspirations as ins}
          <div class="relative pl-8 group">
            <div class="absolute left-0 top-0 bottom-0 w-px bg-slate-200 group-hover:bg-purple-300 transition-colors"></div>
            <div class="absolute left-[-4px] top-2 w-2 h-2 rounded-full bg-slate-300 group-hover:bg-purple-500 transition-colors"></div>
            
            <div class="text-[10px] text-slate-400 font-mono mb-2 flex items-center gap-2">
              {new Date(ins.created_at).toLocaleDateString()} · {ins.theme}
            </div>
            
            <div 
              onclick={() => viewingInspiration = ins}
              class="bg-white border border-slate-100 rounded-2xl p-6 shadow-sm hover:shadow-md hover:border-purple-100 transition-all cursor-pointer group/card"
            >
              <div class="flex justify-between items-start mb-2">
                <h3 class="text-lg font-bold text-slate-800 group-hover/card:text-purple-600 transition-colors">{ins.title}</h3>
                <div class="flex gap-2 opacity-0 group-hover/card:opacity-100 transition-opacity">
                  <button onclick={(e) => { e.stopPropagation(); confirmDelete(ins); }} class="text-slate-300 hover:text-red-400 p-1">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <p class="text-slate-600 text-sm leading-relaxed mb-4 line-clamp-3">{ins.content}</p>
              <div class="flex flex-wrap gap-2">
                {#each ins.tags as tag}
                  <span class="text-[10px] font-medium text-purple-500 bg-purple-50 px-2 py-0.5 rounded-md">#{tag}</span>
                {/each}
              </div>
            </div>
          </div>
        {/each}
        
        {#if !hasMore}
          <div class="text-center py-8 text-slate-300 text-xs tracking-widest uppercase">
            — 到达灵感的尽头 —
          </div>
        {:else}
          <div class="text-center py-8 text-slate-300 text-xs animate-pulse">
            加载更多记忆...
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Floating Add Button -->
  {#if !loading && !listLoading && !addingInspiration}
    <div class="fixed bottom-8 right-8 md:bottom-12 md:right-12 z-20">
      <button 
        onclick={openAddModal}
        class="w-14 h-14 md:w-16 md:h-16 bg-purple-600 text-white rounded-2xl shadow-xl shadow-purple-200 hover:bg-purple-700 hover:scale-105 transition-all flex items-center justify-center"
      >
        <PenLine size={28} />
      </button>
    </div>
  {/if}
</div>

<!-- Modals -->
{#if addingInspiration}
  <div class="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
    <div class="bg-white rounded-[2.5rem] w-full max-w-2xl flex flex-col shadow-2xl overflow-hidden border border-white">
      <div class="p-8 border-b border-slate-50 flex justify-between items-center">
        <div>
          <h3 class="text-2xl font-bold text-slate-800">记录瞬间灵感</h3>
          <p class="text-sm text-slate-400 mt-1">允许混乱，保留情绪</p>
        </div>
        <button onclick={() => addingInspiration = false} class="w-10 h-10 flex items-center justify-center rounded-full bg-slate-50 text-slate-400 hover:bg-slate-100 transition-colors">
          <X size={20} />
        </button>
      </div>
      <div class="p-8">
        <textarea 
          bind:value={inspirationForm.content}
          rows="12"
          placeholder="此刻在想什么？不管是长篇大论还是零碎片段，尽管写下来..."
          class="w-full bg-slate-50/50 border-none rounded-3xl p-6 text-lg text-slate-700 leading-relaxed focus:ring-2 focus:ring-purple-100 transition-all resize-none italic font-serif"
          autofocus
        ></textarea>
        <div class="mt-4 flex items-center gap-2 text-slate-400 text-xs">
          <Sparkles size={14} class="text-purple-400" />
          <span>AI 解释器将负责提炼索引，您的原始内容将原封不动保存</span>
        </div>
      </div>
      <div class="p-8 border-t border-slate-50 flex justify-end gap-4 bg-slate-50/30">
        <button onclick={() => addingInspiration = false} class="px-6 py-3 text-slate-500 font-medium hover:bg-slate-100 rounded-2xl transition">暂时取消</button>
        <button onclick={saveInspiration} disabled={!inspirationForm.content.trim() || inspirationSaving} class="px-10 py-3 bg-purple-600 text-white rounded-2xl font-bold hover:bg-purple-700 disabled:opacity-50 transition shadow-lg shadow-purple-100 flex items-center gap-2">
          {#if inspirationSaving}
            <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <span>AI 正在解释...</span>
          {:else}
            <span>存入灵感库</span>
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if viewingInspiration}
  <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-in fade-in">
    <div class="bg-white rounded-[3rem] w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-white">
      <div class="flex-1 overflow-y-auto p-0 flex flex-col md:flex-row">
        <!-- Left: Original Narrative -->
        <div class="flex-1 p-8 md:p-12 bg-white">
          <div class="flex justify-between items-center mb-8">
            <div class="bg-purple-100 text-purple-600 px-3 py-1 rounded-lg text-xs font-bold tracking-widest uppercase">{viewingInspiration.theme}</div>
            <button onclick={() => viewingInspiration = null} class="md:hidden text-slate-400"><X size={24} /></button>
          </div>
          <h2 class="text-3xl font-bold text-slate-900 mb-6">{viewingInspiration.title}</h2>
          <div class="text-xl text-slate-700 leading-relaxed italic whitespace-pre-wrap font-serif">
            {viewingInspiration.content}
          </div>
        </div>
        
        <!-- Right: AI Interpreter -->
        <div class="w-full md:w-80 p-8 md:p-10 bg-slate-50 border-l border-slate-100 flex flex-col">
          <div class="hidden md:flex justify-end mb-8">
            <button onclick={() => viewingInspiration = null} class="w-10 h-10 flex items-center justify-center rounded-full bg-white text-slate-400 hover:shadow-md transition-all">
              <X size={20} />
            </button>
          </div>
          
          <div class="space-y-8 flex-1">
            <section>
              <div class="text-[10px] text-purple-400 font-bold mb-3 uppercase tracking-widest flex items-center gap-2">
                <Sparkles size={12} />
                AI 解释器旁白
              </div>
              <div class="text-sm text-slate-600 leading-relaxed bg-white p-5 rounded-2xl border border-purple-100 shadow-sm italic relative">
                <div class="absolute -top-2 -left-2 text-purple-200">
                  <MessageSquareQuote size={24} />
                </div>
                "{viewingInspiration.summary}"
              </div>
            </section>
            
            <section>
              <div class="text-[10px] text-slate-400 font-bold mb-3 uppercase tracking-widest flex items-center gap-2">
                弱标签联动
              </div>
              <div class="flex flex-wrap gap-2">
                {#each viewingInspiration.tags as tag}
                  <span class="text-[10px] font-medium bg-white border border-slate-200 text-slate-500 px-3 py-1 rounded-full hover:border-purple-200 transition-colors">#{tag}</span>
                {/each}
              </div>
            </section>
          </div>
          
          <div class="mt-12 pt-8 border-t border-slate-200 flex justify-between items-end">
            <div>
              <div class="text-[10px] text-slate-400 mb-1 uppercase tracking-tighter">记录于</div>
              <div class="text-xs font-mono text-slate-500">{new Date(viewingInspiration.created_at).toLocaleString()}</div>
            </div>
            <button onclick={() => confirmDelete(viewingInspiration)} class="text-red-300 hover:text-red-500 transition-colors">
              <Trash2 size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .inspiration-theme {
    background: linear-gradient(to bottom, #ffffff, #fcfaff);
  }
</style>

