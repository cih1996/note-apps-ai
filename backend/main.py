"""
向量知识库笔记系统 - 命令行界面
Vector Knowledge Base Note System - CLI

一个基于向量匹配的个人笔记系统，无需分类标签，模糊搜索即可找到内容
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from backend.modules.note.service import NoteService
import sys


console = Console()


def print_banner():
    """打印横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║          🧠 向量知识库笔记系统 Vector Notes 🧠            ║
    ║                                                           ║
    ║    无需分类标签，向量匹配，模糊搜索即可找到内容           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_help():
    """打印帮助信息"""
    help_table = Table(title="📚 命令帮助", box=box.ROUNDED, show_header=True)
    help_table.add_column("命令", style="cyan", width=15)
    help_table.add_column("说明", style="green")
    help_table.add_column("示例", style="yellow")
    
    help_table.add_row("add / a", "添加新笔记", "add")
    help_table.add_row("search / s", "搜索笔记", "search 网络穿透")
    help_table.add_row("list / ls", "列出所有笔记", "list")
    help_table.add_row("delete / del", "删除笔记", "delete abc123")
    help_table.add_row("view / v", "查看笔记详情", "view abc123")
    help_table.add_row("help / h", "显示帮助", "help")
    help_table.add_row("quit / q", "退出程序", "quit")
    
    console.print(help_table)


def add_note(service: NoteService):
    """添加笔记"""
    console.print("\n📝 [bold green]添加新笔记[/bold green]")
    console.print("[dim]输入笔记内容，输入空行结束（或输入 'cancel' 取消）[/dim]")
    console.print("[dim]支持多行输入，按两次回车结束[/dim]\n")
    
    lines = []
    empty_count = 0
    
    while True:
        try:
            line = input()
            if line.lower() == 'cancel':
                console.print("[yellow]已取消添加[/yellow]")
                return
            
            if line == "":
                empty_count += 1
                if empty_count >= 1 and lines:  # 一个空行就结束
                    break
                lines.append(line)
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break
    
    content = "\n".join(lines).strip()
    
    if not content:
        console.print("[yellow]笔记内容为空，已取消[/yellow]")
        return
    
    res = service.add_note(content)
    console.print(f"\n[bold green]✅ 笔记已保存！[/bold green] ID: [cyan]{res['id']}[/cyan]")
    console.print(Panel(content[:200] + ("..." if len(content) > 200 else ""), 
                       title="笔记预览", border_style="green"))


def search_notes(service: NoteService, query: str = None):
    """搜索笔记"""
    if not query:
        query = Prompt.ask("\n🔍 请输入搜索内容")
    
    if not query.strip():
        console.print("[yellow]搜索内容不能为空[/yellow]")
        return
    
    console.print(f"\n[dim]正在搜索: {query}[/dim]")
    
    results = service.search_notes(query, top_k=5)
    
    if not results:
        console.print("[yellow]未找到相关笔记[/yellow]")
        return
    
    console.print(f"\n[bold green]找到 {len(results)} 条相关笔记：[/bold green]\n")
    
    for i, note in enumerate(results, 1):
        if note['similarity'] >= 70:
            sim_color = "green"
        elif note['similarity'] >= 50:
            sim_color = "yellow"
        else:
            sim_color = "red"
        
        content_preview = note['content'][:300]
        if len(note['content']) > 300:
            content_preview += "..."
        
        title = f"#{i} [cyan]{note['id']}[/cyan] | 相似度: [{sim_color}]{note['similarity']}%[/{sim_color}]"
        console.print(Panel(content_preview, title=title, border_style=sim_color, box=box.ROUNDED))


def list_notes(service: NoteService):
    """列出所有笔记"""
    notes = service.get_all_notes()
    
    if not notes:
        console.print("[yellow]知识库为空，快添加第一条笔记吧！[/yellow]")
        return
    
    table = Table(title=f"📋 所有笔记 (共 {len(notes)} 条)", box=box.ROUNDED)
    table.add_column("ID", style="cyan", width=10)
    table.add_column("内容预览", style="white", max_width=60)
    table.add_column("创建时间", style="dim", width=20)
    
    for note in notes:
        content_preview = note['content'][:80].replace('\n', ' ')
        if len(note['content']) > 80:
            content_preview += "..."
        
        created_at = note.get('created_at', '未知')[:19]
        table.add_row(note['id'], content_preview, created_at)
    
    console.print(table)


def view_note(service: NoteService, note_id: str = None):
    """查看笔记详情"""
    if not note_id:
        note_id = Prompt.ask("请输入笔记ID")
    
    note = service.get_note_by_id(note_id)
    
    if not note:
        console.print(f"[red]未找到ID为 {note_id} 的笔记[/red]")
        return
    
    created_at = note.get('created_at', '未知')
    char_count = note.get('char_count', len(note['content']))
    
    console.print(f"\n[bold]笔记详情[/bold] - ID: [cyan]{note_id}[/cyan]")
    console.print(f"[dim]创建时间: {created_at} | 字数: {char_count}[/dim]\n")
    console.print(Panel(note['content'], border_style="cyan", box=box.DOUBLE))


def delete_note(service: NoteService, note_id: str = None):
    """删除笔记"""
    if not note_id:
        note_id = Prompt.ask("请输入要删除的笔记ID")
    
    note = service.get_note_by_id(note_id)
    
    if not note:
        console.print(f"[red]未找到ID为 {note_id} 的笔记[/red]")
        return
    
    console.print(Panel(note['content'][:200], title="即将删除的笔记", border_style="red"))
    
    if Confirm.ask("确定要删除这条笔记吗？"):
        if service.delete_note(note_id):
            console.print("[green]✅ 笔记已删除[/green]")
        else:
            console.print("[red]删除失败[/red]")
    else:
        console.print("[yellow]已取消删除[/yellow]")


def main():
    """主函数"""
    print_banner()
    
    console.print("[dim]正在加载知识库...[/dim]")
    service = NoteService()
    
    console.print(f"\n[green]知识库已就绪！[/green] 输入 [cyan]help[/cyan] 查看帮助\n")
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]📌 Notes[/bold cyan]").strip()
            
            if not user_input:
                continue
            
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else None
            
            if cmd in ['quit', 'q', 'exit']:
                console.print("[cyan]👋 再见！[/cyan]")
                break
            
            elif cmd in ['help', 'h', '?']:
                print_help()
            
            elif cmd in ['add', 'a', 'new']:
                add_note(service)
            
            elif cmd in ['search', 's', 'find', 'f']:
                search_notes(service, args)
            
            elif cmd in ['list', 'ls', 'all']:
                list_notes(service)
            
            elif cmd in ['view', 'v', 'show', 'get']:
                view_note(service, args)
            
            elif cmd in ['delete', 'del', 'rm', 'remove']:
                delete_note(service, args)
            
            else:
                console.print(f"[dim]未知命令，将作为搜索内容处理...[/dim]")
                search_notes(service, user_input)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]按 Ctrl+C 退出，或输入 quit 退出[/yellow]")
        except Exception as e:
            console.print(f"[red]发生错误: {e}[/red]")


if __name__ == "__main__":
    main()
