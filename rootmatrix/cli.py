import sys
import os
import json
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

def _get_ide_configs():
    home = Path.home()
    if sys.platform == "win32":
        appdata = Path(os.getenv("APPDATA", home / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        appdata = home / "Library" / "Application Support"
    else:
        appdata = home / ".config"

    return {
        "cursor": home / ".cursor" / "mcp.json",
        "windsurf": home / ".codeium" / "windsurf" / "mcp_config.json",
        "trae": home / ".trae" / "mcp.json",
        "claude-desktop": appdata / "Claude" / "claude_desktop_config.json",
        "cline": appdata / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        "roocode": appdata / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json",
    }

SERVER_ENTRY = {
    "command": sys.executable,
    "args": ["-m", "rootmatrix.server"],
    "env": {},
    "disabled": False
}

class RootMatrixGroup(click.Group):
    def get_help(self, ctx):
        BANNER = """██████╗  ██████╗  ██████╗ ████████╗███╗   ███╗ █████╗ ████████╗██████╗ ██╗██╗  ██╗
██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝████╗ ████║██╔══██╗╚══██╔══╝██╔══██╗██║╚██╗██╔╝
██████╔╝██║   ██║██║   ██║   ██║   ██╔████╔██║███████║   ██║   ██████╔╝██║ ╚███╔╝
██╔══██╗██║   ██║██║   ██║   ██║   ██║╚██╔╝██║██╔══██║   ██║   ██╔══██╗██║ ██╔██╗
██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║ ╚═╝ ██║██║  ██║   ██║   ██║  ██║██║██╔╝ ██╗
╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝"""

        SMALL_BANNER = """█▀█ █▀█ █▀█ ▀█▀ █▀▄▀█ ▄▀█ ▀█▀ █▀█ █ ▀▄▀
█▀▄ █▄█ █▄█  █  █ ▀ █ █▀█  █  █▀▄ █ █ █"""

        SAFE_ASCII = """  ___           _   __  __      _      _     
 | _ \\___ ___ _| |_|  \\/  |__ _| |_ _ _(_)_ __ 
 |   / _ \\ _ \\  _| | |\\/| / _` |  _| '_| \\ \\ / 
 |_|_\\___/\\___/\\__|_|_  |_\\__,_|\\__|_| |_/_\\_\\ """

        try:
            active_banner = BANNER if console.width >= 86 else SMALL_BANNER
            text = Text("\n", justify="center")
            text.append(active_banner, style="bold bright_magenta")
            text.append("\n\nAI-Powered CLI Toolkit\n", style="dim bright_magenta")
            console.print(text, crop=True)
        except UnicodeEncodeError:
            # Fallback for old Windows CMDs stuck on CP1252
            text = Text("\n", justify="center")
            text.append(SAFE_ASCII, style="bold bright_magenta")
            text.append("\n\nAI-Powered CLI Toolkit\n", style="dim bright_magenta")
            console.print(text, crop=True)
            
        return super().get_help(ctx)

@click.group(cls=RootMatrixGroup)
def main():
    """RootMatrix CLI"""
    pass

@main.command()
@click.argument('ide', type=click.Choice(['cursor', 'windsurf', 'trae', 'claude-desktop', 'cline', 'roocode', 'all']), default='all')
def init(ide):
    """Initializes the RootMatrix MCP server in the specified IDE."""
    ide_configs = _get_ide_configs()
    targets = ide_configs.keys() if ide == 'all' else [ide]

    for target in targets:
        path = ide_configs[target]
        config = {}
        
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            try:
                config = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                console.print(f"[bold yellow][WARNING][/bold yellow] {path} contains invalid JSON. Fix it manually first.")
                continue

        config.setdefault("mcpServers", {})["rootmatrix"] = SERVER_ENTRY
        
        try:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(config, indent=2), encoding="utf-8")
            tmp.replace(path)
            console.print(f"[bold green][SUCCESS][/bold green] Injected RootMatrix into [cyan]{target}[/cyan] ({path})")
        except Exception as e:
            console.print(f"[bold red][ERROR][/bold red] Failed to inject into {target}: {e}")
            
    console.print("\n[bold yellow][INFO][/bold yellow] If your IDE (like Cursor on Windows) requires manual UI configuration, add this server:")
    console.print(json.dumps({"mcpServers": {"rootmatrix": SERVER_ENTRY}}, indent=2))
    console.print("\n[bold yellow][INFO][/bold yellow] Restart your IDE or refresh the MCP connections to apply changes.")

@main.command()
def init_project():
    """Initializes RootMatrix configurations for the current project."""
    cwd = Path.cwd()
    cg_dir = cwd / ".rootmatrix"
    
    # Create required directories
    (cg_dir / "vectordb").mkdir(parents=True, exist_ok=True)
    
    # Generate AI Rules for auto-enforcement (do this even if already initialized)
    rule_content = """
# 🧠 RootMatrix Context Management Rules
You are connected to the RootMatrix MCP Server. To protect your context window, maximize generation speed, and prevent token exhaustion, you MUST adhere to these strict rules:

1. **NEVER read full files immediately.** You must ALWAYS use `read_optimized_file` first to get a structural skeleton (AST) of the file.
2. **BE SURGICAL.** If you need to edit a specific function, use `read_function` to extract ONLY that function's body.
3. **EXPLORE SAFELY.** Use `get_project_map` to understand the workspace structure before blindly guessing paths.
4. **SEMANTIC SEARCH FIRST.** Do not use native ripgrep for conceptual searches. Use the `search_codebase` tool to perform local ChromaDB RAG queries.
5. **TRACK REFERENCES.** Use `find_references` to map dependencies safely before making breaking changes.
6. **LAST RESORT ONLY.** You may ONLY use `read_raw_file` if you are performing a massive file-wide refactor and have explicitly checked that your context budget allows for it via `get_context_budget`.
"""
    for rules_file in [".cursorrules", ".windsurfrules"]:
        rules_path = cwd / rules_file
        if rules_path.exists():
            current_content = rules_path.read_text(encoding="utf-8")
            if "# 🧠 RootMatrix Context Management Rules" not in current_content:
                rules_path.write_text(current_content.rstrip() + "\n\n" + rule_content.strip() + "\n", encoding="utf-8")
        else:
            rules_path.write_text(rule_content.strip() + "\n", encoding="utf-8")
    
    if (cg_dir / "config.json").exists():
        console.print(f"[bold yellow][WARNING][/bold yellow] RootMatrix is already initialized in {cwd}. Updated AI rules.")
        return
        
    # Generate config.json
    config_content = {
        "exclude_patterns": ["node_modules", ".git", "__pycache__", "venv", ".env", ".rootmatrix"]
    }
    (cg_dir / "config.json").write_text(json.dumps(config_content, indent=2), encoding="utf-8")

    console.print(f"[bold green][SUCCESS][/bold green] RootMatrix initialized in [cyan]{cwd}[/cyan]")
    console.print("Created [bold].rootmatrix[/bold] directory and auto-enforcement AI rules.")
    
    # Create .gitignore so vector DB is not committed
    gitignore_path = cg_dir / ".gitignore"
    gitignore_path.write_text("vectordb/\n", encoding="utf-8")

@main.command()
def index_project():
    """Indexes the entire project into the local vector DB for semantic search."""
    cwd = Path.cwd()
    cg_dir = cwd / ".rootmatrix"
    
    if not cg_dir.exists():
        console.print("[bold red][ERROR][/bold red] Not a RootMatrix project. Run 'rootmatrix init-project' first.")
        return
        
    from rootmatrix.engine.filter import raw_file
    from rootmatrix.engine.vector_store import upsert_files
    from rootmatrix.engine.config import load_config
    
    config = load_config(str(cwd / "dummy.txt"))
    excludes = set(config.get("exclude_patterns", ["node_modules", ".git", "__pycache__", "venv", ".env", ".rootmatrix"]))
    valid_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt'}

    files_to_index = []
    
    with console.status("[bold blue]Scanning files...", spinner="dots"):
        for root, dirs, files in os.walk(cwd):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in excludes and not d.startswith('.')]
            
            for file in files:
                path = Path(root) / file
                if path.suffix.lower() in valid_exts and file not in excludes:
                    try:
                        content, _ = raw_file(str(path))
                        if not content.startswith("# could not read file"):
                            files_to_index.append({
                                "path": str(path),
                                "content": content
                            })
                    except Exception as e:
                        console.print(f"[yellow]Skipping {file}: {e}[/yellow]")
    
    if files_to_index:
        with console.status(f"[bold blue]Indexing {len(files_to_index)} files into Vector DB...", spinner="bouncingBar"):
            upsert_files(str(cwd / "dummy.txt"), files_to_index)
        console.print(f"[bold green][SUCCESS][/bold green] Project indexing complete! {len(files_to_index)} files added.")
    else:
        console.print("[bold yellow][WARNING][/bold yellow] No indexable files found.")

@main.command()
def watch():
    """Starts a background daemon to watch for file changes and sync the Vector DB."""
    cwd = Path.cwd()
    cg_dir = cwd / ".rootmatrix"
    
    if not cg_dir.exists():
        console.print("[bold red][ERROR][/bold red] Not a RootMatrix project. Run 'rootmatrix init-project' first.")
        return
        
    try:
        import time
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        console.print("[bold red][ERROR][/bold red] Watchdog not installed. Run 'pip install watchdog' or 'pip install -e .'")
        return
        
    from rootmatrix.engine.filter import raw_file
    from rootmatrix.engine.vector_store import upsert_files, delete_file
    from rootmatrix.engine.config import load_config
    
    config = load_config(str(cwd / "dummy.txt"))
    excludes = set(config.get("exclude_patterns", ["node_modules", ".git", "__pycache__", "venv", ".env", ".rootmatrix"]))
    valid_exts = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt'}

    class SyncHandler(FileSystemEventHandler):
        def _is_valid(self, path_str: str) -> bool:
            path_obj = Path(path_str)
            if path_obj.suffix.lower() not in valid_exts:
                return False
            # Check if any parent dir is in excludes
            for part in path_obj.parts:
                if part in excludes or part.startswith('.'):
                    # Exception for cwd
                    if part == str(cwd.name): continue
                    if part != '.':
                        return False
            return True

        def on_created(self, event):
            if not event.is_directory and self._is_valid(event.src_path):
                self._upsert(event.src_path)

        def on_modified(self, event):
            if not event.is_directory and self._is_valid(event.src_path):
                self._upsert(event.src_path)

        def on_deleted(self, event):
            if not event.is_directory and self._is_valid(event.src_path):
                console.print(f"[bold red][-][/bold red] Deleted: {event.src_path}")
                delete_file(str(cwd / "dummy.txt"), event.src_path)

        def _upsert(self, path_str: str):
            try:
                content, _ = raw_file(path_str)
                if not content.startswith("# could not read file"):
                    console.print(f"[bold green][+][/bold green] Upserted: {path_str}")
                    upsert_files(str(cwd / "dummy.txt"), [{"path": path_str, "content": content}])
            except Exception as e:
                console.print(f"[bold yellow][!][/bold yellow] Failed to upsert {path_str}: {e}")

    event_handler = SyncHandler()
    observer = Observer()
    observer.schedule(event_handler, str(cwd), recursive=True)
    observer.start()
    
    console.print(f"[bold cyan][*][/bold cyan] RootMatrix Watcher started in [bold]{cwd}[/bold]")
    console.print("[bold cyan][*][/bold cyan] Monitoring for file changes... (Press Ctrl+C to stop)")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        console.print("\n[bold cyan][*][/bold cyan] Watcher stopped.")
    observer.join()

@main.command()
def status():
    """Shows the current token usage and RootMatrix status in a beautiful terminal panel."""
    from rootmatrix.engine.budget import get_budget_status
    
    cwd = Path.cwd()
    budget = get_budget_status(str(cwd / "dummy.txt"))
    
    used = budget['tokens_used']
    limit = budget['daily_limit']
    remaining = budget['remaining']
    usage_pct = (used / limit) * 100 if limit > 0 else 0
    
    # Color logic
    color = "green"
    if usage_pct > 75:
        color = "yellow"
    if usage_pct > 90:
        color = "red"
        
    status_text = Text()
    status_text.append(f"Tokens Used Today: ", style="bold white")
    status_text.append(f"{used:,}\n", style=f"bold {color}")
    
    status_text.append(f"Daily Limit:       ", style="bold white")
    status_text.append(f"{limit:,}\n", style="cyan")
    
    status_text.append(f"Remaining:         ", style="bold white")
    status_text.append(f"{remaining:,}\n", style=f"bold {color}")
    
    status_text.append(f"Usage:             ", style="bold white")
    status_text.append(f"{usage_pct:.1f}%\n\n", style=f"bold {color}")
    
    status_text.append("[ACTIVE] ", style="bold green")
    status_text.append("RootMatrix is actively monitoring and optimizing your context window.")
    
    panel = Panel(
        status_text,
        title="[bold magenta]RootMatrix Engine Status[/bold magenta]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)

if __name__ == '__main__':
    main()
