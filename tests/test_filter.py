import os
from pathlib import Path
from rootmatrix.engine.filter import _ast_skeleton, _strip_comments, optimize_file

FIXTURE_DIR = Path(__file__).parent / "fixtures"

def test_ast_skeleton():
    sample_path = FIXTURE_DIR / "sample.py"
    content = sample_path.read_text(encoding="utf-8")
    
    skel = _ast_skeleton(content)
    
    assert "def calculate_metrics(data: dict) -> float: ..." in skel
    assert "class Processor: ..." in skel
    assert "def __init__(self): ..." in skel
    assert "async def process_async(self, item): ..." in skel
    
    # Check that bodies are removed
    assert "total = sum(data.values())" not in skel
    assert "self.ready = True" not in skel

def test_strip_comments():
    content = "x = 1 # some comment\n\ny = 2\n"
    stripped = _strip_comments(content)
    assert "some comment" not in stripped
    assert "x = 1" in stripped
    assert "y = 2" in stripped

def test_optimize_file():
    sample_path = FIXTURE_DIR / "sample.py"
    skel, count = optimize_file(str(sample_path))
    assert count > 0
    assert "def calculate_metrics" in skel

def test_optimize_file_javascript():
    sample_path = FIXTURE_DIR / "sample.js"
    skel, count = optimize_file(str(sample_path))
    assert count > 0
    assert "function calculateMetrics(data) {" in skel
    assert "class Processor {" in skel
    assert "async processAsync(item) {" in skel
    assert "const helper = (a, b) => {" in skel
    
    # Ensure bodies are removed
    assert "Object.values" not in skel
    assert "this.ready = true" not in skel

def test_optimize_file_fastapi():
    sample_path = FIXTURE_DIR / "sample_api.py"
    skel, count = optimize_file(str(sample_path))
    assert count > 0
    # Make sure decorators are retained
    assert "@app.get(\"/\")" in skel
    assert "def read_root(): ..." in skel
    assert "@app.get(\"/items/{item_id}\")" in skel
    assert "async def read_item(item_id: int, q: str = None): ..." in skel
    
    # Ensure bodies are removed
    assert "db = get_db()" not in skel

def test_optimize_file_react():
    sample_path = FIXTURE_DIR / "sample.tsx"
    skel, count = optimize_file(str(sample_path))
    assert count > 0
    # Make sure component is retained
    assert "export const MyComponent = ({ title }: { title: string }) => {" in skel
    # Ensure business logic/JSX body is largely stripped from variables/functions
    assert "<h1>{title}</h1>" not in skel

from rootmatrix.engine.filter import extract_function

def test_extract_function():
    sample_path = FIXTURE_DIR / "sample.py"
    func, count = extract_function(str(sample_path), "calculate_metrics")
    assert count > 0
    assert "def calculate_metrics(data: dict) -> float:" in func
    # The body should be present, unlike in optimize_file
    assert "total = sum(data.values())" in func
    assert "return float(total)" in func
