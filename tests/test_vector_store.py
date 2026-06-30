import pytest
from pathlib import Path
from rootmatrix.engine.vector_store import upsert_files, search

def test_vector_store_upsert_and_search(tmp_path):
    # Setup dummy project
    cg_dir = tmp_path / ".rootmatrix"
    cg_dir.mkdir()
    
    dummy_file = tmp_path / "test.py"
    dummy_file.write_text("print('hello')")
    
    # 1. Upsert
    files_data = [
        {
            "path": str(dummy_file),
            "content": "def calculate_taxes(income): return income * 0.2"
        },
        {
            "path": str(tmp_path / "other.py"),
            "content": "def hello_world(): print('Hello')"
        }
    ]
    
    upsert_files(str(dummy_file), files_data)
    
    # 2. Search
    results = search(str(dummy_file), "tax calculation", n_results=1)
    
    assert len(results) == 1
    assert "calculate_taxes" in results[0]["content"]
    assert results[0]["metadata"]["path"] == str(dummy_file)
