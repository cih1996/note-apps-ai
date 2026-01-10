<script>
  import { BookOpen, Sparkles, Database, ListTodo } from 'lucide-svelte';
  import NoteSection from './lib/NoteSection.svelte';
  import InspirationSection from './lib/InspirationSection.svelte';
  import TodoSection from './lib/TodoSection.svelte';

  let currentTab = $state('note'); // 'note', 'inspiration', or 'todo'
</script>

<div class="max-w-5xl mx-auto h-screen flex flex-col md:p-4 p-0">
  <!-- Header -->
  <header class="flex items-center justify-between mb-4 md:mb-8 px-4 pt-4 md:pt-0">
    <div class="flex items-center space-x-3 md:space-x-6">
      <div class="flex items-center space-x-2">
        <div class="bg-primary p-2 md:p-2.5 rounded-lg md:rounded-xl text-white shadow-lg shadow-blue-100">
          <Database size={20} class="md:w-6 md:h-6" />
        </div>
        <h1 class="text-xl font-black text-slate-800 hidden sm:block tracking-tight">知识库 <span class="text-primary">CORE</span></h1>
      </div>
      
      <!-- Tab Switcher -->
      <nav class="flex bg-slate-200/50 p-1 md:p-1.5 rounded-xl md:rounded-2xl backdrop-blur-sm border border-white">
        <button 
          onclick={() => currentTab = 'note'}
          class="flex items-center gap-1 md:gap-2 px-3 md:px-6 py-2 rounded-lg md:rounded-xl text-sm font-bold transition-all {currentTab === 'note' ? 'bg-white shadow-md text-primary translate-y-[-1px]' : 'text-slate-500 hover:text-slate-700'}"
        >
          <BookOpen size={16} />
          <span class="hidden min-[400px]:inline">笔记</span>
        </button>
        <button 
          onclick={() => currentTab = 'inspiration'}
          class="flex items-center gap-1 md:gap-2 px-3 md:px-6 py-2 rounded-lg md:rounded-xl text-sm font-bold transition-all {currentTab === 'inspiration' ? 'bg-white shadow-md text-purple-600 translate-y-[-1px]' : 'text-slate-500 hover:text-slate-700'}"
        >
          <Sparkles size={16} />
          <span class="hidden min-[400px]:inline">灵感</span>
        </button>
        <button 
          onclick={() => currentTab = 'todo'}
          class="flex items-center gap-1 md:gap-2 px-3 md:px-6 py-2 rounded-lg md:rounded-xl text-sm font-bold transition-all {currentTab === 'todo' ? 'bg-white shadow-md text-blue-600 translate-y-[-1px]' : 'text-slate-500 hover:text-slate-700'}"
        >
          <ListTodo size={16} />
          <span class="hidden min-[400px]:inline">待办</span>
        </button>
      </nav>
    </div>

    <div class="hidden md:flex items-center gap-4">
      <div class="text-[10px] text-slate-400 font-bold uppercase tracking-[0.2em] bg-slate-100 px-3 py-1 rounded-full border border-slate-200">AI Powered Node</div>
    </div>
  </header>

  <!-- Main Content Area -->
  <main class="flex-1 flex flex-col min-h-0 relative">
    {#if currentTab === 'note'}
      <NoteSection />
    {:else if currentTab === 'inspiration'}
      <InspirationSection />
    {:else}
      <TodoSection />
    {/if}
  </main>


</div>

<style>
  :global(.animate-in) {
    animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: scale(0.98) translateY(10px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }
</style>
