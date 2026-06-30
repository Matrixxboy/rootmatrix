import os
import json
from pathlib import Path
from rootmatrix.engine.config import load_config, find_project_root

def test_find_project_root(tmp_path):
    cg_dir = tmp_path / ".rootmatrix"
    cg_dir.mkdir()
    
    sub_dir = tmp_path / "src" / "deep"
    sub_dir.mkdir(parents=True)
    
    # Create dummy file
    dummy = sub_dir / "test.py"
    dummy.write_text("print('hello')")
    
    root = find_project_root(str(dummy))
    assert root == tmp_path

def test_load_config(tmp_path):
    cg_dir = tmp_path / ".rootmatrix"
    cg_dir.mkdir()
    
    local_config = cg_dir / "config.json"
    local_config.write_text(json.dumps({"daily_limit": 500, "custom_key": "val"}))
    
    dummy = tmp_path / "test.py"
    dummy.write_text("print('hello')")
    
    config = load_config(str(dummy))
    assert config["daily_limit"] == 500
    assert config["custom_key"] == "val"
    assert "exclude_patterns" in config # From default
