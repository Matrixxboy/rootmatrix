import os
from pathlib import Path

# Directories to ignore when mapping the project
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", "venv", ".venv", "env",
    ".env", "dist", "build", "coverage", ".pytest_cache", ".idea", ".vscode"
}

def generate_map(dir_path: str = ".") -> str:
    """
    Generates a tree representation of the workspace.
    Useful for AI agents to understand the high-level layout.
    """
    root = Path(dir_path).resolve()
    if not root.exists() or not root.is_dir():
        return f"# Error: {dir_path} is not a valid directory."

    tree_str = []
    
    def walk_dir(current_path: Path, prefix: str = ""):
        try:
            # Sort directories first, then files, both alphabetically
            entries = list(current_path.iterdir())
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            # Filter out ignored directories
            entries = [e for e in entries if not (e.is_dir() and e.name in IGNORE_DIRS)]
            
            for i, entry in enumerate(entries):
                is_last = (i == len(entries) - 1)
                connector = "└── " if is_last else "├── "
                
                tree_str.append(f"{prefix}{connector}{entry.name}")
                
                if entry.is_dir():
                    extension = "    " if is_last else "│   "
                    walk_dir(entry, prefix + extension)
        except PermissionError:
            tree_str.append(f"{prefix}└── [Permission Denied]")
            
    tree_str.append(root.name + "/")
    walk_dir(root)
    
    return "\n".join(tree_str)
