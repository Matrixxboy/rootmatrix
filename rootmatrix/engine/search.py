import subprocess
from pathlib import Path
from . import tokenizer

def find_references_in_workspace(dir_path: str, symbol_name: str) -> dict:
    """
    Searches for references of a symbol across the workspace using ripgrep.
    Returns truncated lines to save context tokens.
    """
    root = Path(dir_path).resolve()
    if not root.exists() or not root.is_dir():
        return {"error": f"Invalid directory: {dir_path}", "tokens_used": 0}
        
    try:
        # We rely on rg (ripgrep) if available, or just a simple python search if not.
        # But this assumes we want an exact match for a symbol name (word boundary).
        # We will use python's pathlib for platform independence and simplicity if rg is missing.
        # Given it's a FastMCP server, keeping it python-native is safer.
        
        results = []
        tokens_used = 0
        
        # Walk and search in python (slower but guaranteed to work without external binaries)
        # ignoring obvious dirs
        IGNORE_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
        
        for p in root.rglob("*"):
            if p.is_file() and not any(part in IGNORE_DIRS for part in p.parts):
                try:
                    # Skip common binary/large files
                    if p.suffix.lower() in {'.sqlite', '.db', '.pyc', '.png', '.jpg', '.exe', '.dll', '.zip', '.tar', '.gz'}:
                        continue
                        
                    content = p.read_text(encoding='utf-8', errors='ignore')
                    lines = content.splitlines()
                    
                    file_matches = []
                    # Simple text match (could use regex \b for word boundary)
                    for i, line in enumerate(lines):
                        if symbol_name in line:
                            # Truncate very long lines
                            display_line = line.strip()
                            if len(display_line) > 120:
                                display_line = display_line[:117] + "..."
                            file_matches.append(f"  Line {i+1}: {display_line}")
                            
                    if file_matches:
                        results.append(f"File: {p.relative_to(root)}")
                        results.extend(file_matches)
                        
                        # Stop if we found way too many to save tokens
                        if len(results) > 100:
                            results.append("... [Too many results, truncated] ...")
                            break
                            
                except Exception:
                    pass
                    
        result_text = "\n".join(results) if results else f"No references found for '{symbol_name}'."
        tokens = tokenizer.count(result_text)
        
        return {
            "content": result_text,
            "tokens_used": tokens
        }
    except Exception as e:
        return {"error": str(e), "tokens_used": 0}
