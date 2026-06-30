import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

GLOBAL_CONFIG_PATH = Path.home() / ".rootmatrix" / "config.json"
PROJECT_DIR_NAME = ".rootmatrix"

def find_project_root(start_path: str) -> Optional[Path]:
    """
    Traverse upwards from start_path to find the directory containing .rootmatrix.
    Falls back to .git if .rootmatrix is not found, but we prefer .rootmatrix.
    """
    current = Path(start_path).resolve()
    if not current.is_dir():
        current = current.parent
        
    while current.parent != current: # Stop at root
        if (current / PROJECT_DIR_NAME).is_dir():
            return current
        current = current.parent
        
    # Fallback to .git if no .rootmatrix found
    current = Path(start_path).resolve()
    if not current.is_dir():
        current = current.parent
    while current.parent != current:
        if (current / ".git").is_dir():
            return current
        current = current.parent
        
    return None

def load_config(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration. Merges global config with project-local config.
    """
    config = {
        "daily_limit": int(os.getenv("CG_DAILY_LIMIT", 200000)),
        "exclude_patterns": ["node_modules", ".git", "__pycache__", "venv", ".env"],
    }
    
    # 1. Load global config
    if GLOBAL_CONFIG_PATH.exists():
        try:
            global_conf = json.loads(GLOBAL_CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(global_conf)
        except Exception:
            pass

    # 2. Load project-local config
    if file_path:
        root = find_project_root(file_path)
        if root:
            local_config_path = root / PROJECT_DIR_NAME / "config.json"
            if local_config_path.exists():
                try:
                    local_conf = json.loads(local_config_path.read_text(encoding="utf-8"))
                    config.update(local_conf)
                except Exception:
                    pass
                    
    return config
