import ast
import re
import hashlib
from pathlib import Path
from typing import Tuple
import tree_sitter_javascript as ts_js
import tree_sitter_typescript as ts_ts
from tree_sitter import Language, Parser

from . import tokenizer

def _file_hash(path: str) -> str:
    """Returns a quick SHA256 hash of the file contents for caching (if implemented)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in chunks for large files
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def _tree_sitter_skeleton(path: str, content: str) -> str:
    """Uses tree-sitter to extract skeleton for supported languages."""
    ext = Path(path).suffix.lower()
    
    # Supported languages mapped to their parsers
    GRAMMARS = {
        ".js": (ts_js.language(), "javascript"),
        ".jsx": (ts_ts.language_tsx(), "tsx"),
        ".ts": (ts_ts.language_typescript(), "typescript"),
        ".tsx": (ts_ts.language_tsx(), "tsx"),
    }
    
    if ext not in GRAMMARS:
        raise ValueError(f"Unsupported extension for tree-sitter: {ext}")
        
    grammar, lang_name = GRAMMARS[ext]
    lang = Language(grammar)
    parser = Parser(lang)
    
    tree = parser.parse(content.encode("utf-8"))
    lines = content.splitlines()
    skeleton_lines = []
    
    # Query to find structure
    # This is a basic query. Depending on the language, query might differ.
    # But for JS/TS, function_declaration, class_declaration are common.
    
    query_str = """
    (function_declaration) @func
    (class_declaration) @class
    (method_definition) @method
    """
    
    # We will just traverse the AST for simplicity instead of querying
    # because tree-sitter python bindings for queries can sometimes be finicky
    # across different grammar versions.
    
    def traverse(node):
        nodes_to_keep = []
        
        # JS/TS node types
        target_types = {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "arrow_function",
            "variable_declarator" # Often holds arrow functions
        }
        
        if node.type in target_types:
            nodes_to_keep.append(node)
            # Do not traverse children of a function to avoid inner bodies
            # But we do traverse classes to get their methods.
            if node.type == "class_declaration":
                for child in node.children:
                    nodes_to_keep.extend(traverse(child))
        else:
            for child in node.children:
                nodes_to_keep.extend(traverse(child))
                
        return nodes_to_keep
        
    nodes_to_keep = traverse(tree.root_node)
    
    # Ensure they are sorted by line
    nodes_to_keep.sort(key=lambda n: n.start_point[0])
    
    for node in nodes_to_keep:
        # Avoid extracting just variables unless they are arrows
        if node.type == "variable_declarator":
            is_arrow = any(c.type == "arrow_function" for c in node.children)
            if not is_arrow:
                continue
                
        start_line = node.start_point[0]
        sig_str = lines[start_line].strip()
        skeleton_lines.append(sig_str + " ...")
        
    if not skeleton_lines:
        raise ValueError("No structural nodes found")
        
    return "\n".join(skeleton_lines)

def _ast_skeleton(content: str) -> str:
    """Uses Python's stdlib ast to extract class and function signatures."""
    tree = ast.parse(content)
    lines = content.splitlines()
    
    skeleton_lines = []
    
    # We will do a very basic skeletonization:
    # Just grab the lines defining classes and functions.
    # A real implementation would use an AST visitor to reconstruct
    # the code or properly slice the lines, but this is a V1 start.
    
    class SkeletonVisitor(ast.NodeVisitor):
        def __init__(self):
            self.nodes_to_keep = []
            
        def visit_ClassDef(self, node):
            self.nodes_to_keep.append(node)
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            self.nodes_to_keep.append(node)
            # Do not visit children of functions to avoid keeping inner methods
            
        def visit_AsyncFunctionDef(self, node):
            self.nodes_to_keep.append(node)
            
    visitor = SkeletonVisitor()
    visitor.visit(tree)
    
    # Better extraction that preserves decorators
    for node in visitor.nodes_to_keep:
        start_line = node.lineno - 1
        
        # Capture decorators (like @app.get)
        if hasattr(node, 'decorator_list') and node.decorator_list:
            start_line = node.decorator_list[0].lineno - 1
            
        for i in range(start_line, node.lineno - 1):
            skeleton_lines.append(lines[i].strip())
            
        # The actual signature line
        sig_str = lines[node.lineno - 1].strip()
        skeleton_lines.append(sig_str + " ...")
        
    return "\n".join(skeleton_lines)

def _tree_sitter_extract_function(path: str, content: str, func_name: str) -> str:
    """Uses tree-sitter to extract a specific function body."""
    ext = Path(path).suffix.lower()
    
    GRAMMARS = {
        ".js": (ts_js.language(), "javascript"),
        ".jsx": (ts_ts.language_tsx(), "tsx"),
        ".ts": (ts_ts.language_typescript(), "typescript"),
        ".tsx": (ts_ts.language_tsx(), "tsx"),
    }
    
    if ext not in GRAMMARS:
        raise ValueError(f"Unsupported extension for tree-sitter: {ext}")
        
    grammar, lang_name = GRAMMARS[ext]
    lang = Language(grammar)
    parser = Parser(lang)
    
    tree = parser.parse(content.encode("utf-8"))
    content_bytes = content.encode("utf-8")
    
    def traverse_find(node):
        target_types = {
            "function_declaration",
            "method_definition",
            "arrow_function",
            "variable_declarator"
        }
        
        # Check if this node matches our function name
        if node.type in target_types:
            # Identifier is usually a child of function_declaration or variable_declarator
            for child in node.children:
                if child.type == "identifier" or child.type == "property_identifier":
                    name = content_bytes[child.start_byte:child.end_byte].decode("utf-8")
                    if name == func_name:
                        return node
        
        # Recurse
        for child in node.children:
            result = traverse_find(child)
            if result:
                return result
        return None
        
    found_node = traverse_find(tree.root_node)
    
    if not found_node:
        raise ValueError(f"Function {func_name} not found using tree-sitter")
        
    return content_bytes[found_node.start_byte:found_node.end_byte].decode("utf-8")

def _ast_extract_function(content: str, func_name: str) -> str:
    """Uses Python's stdlib ast to extract a specific function body."""
    tree = ast.parse(content)
    lines = content.splitlines()
    
    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self):
            self.found_node = None
            
        def visit_FunctionDef(self, node):
            if node.name == func_name:
                self.found_node = node
            self.generic_visit(node)
            
        def visit_AsyncFunctionDef(self, node):
            if node.name == func_name:
                self.found_node = node
            self.generic_visit(node)
            
        def visit_ClassDef(self, node):
            # Still visit classes to find methods
            self.generic_visit(node)
            
    visitor = FunctionVisitor()
    visitor.visit(tree)
    
    if not visitor.found_node:
        raise ValueError(f"Function {func_name} not found using AST")
        
    node = visitor.found_node
    start_line = node.lineno - 1
    end_line = node.end_lineno
    
    # Capture decorators
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start_line = node.decorator_list[0].lineno - 1
        
    return "\n".join(lines[start_line:end_line])

def _strip_comments(content: str) -> str:
    """Fallback 3: Strips comments using regex."""
    # Strip single line comments
    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
    # Strip empty lines
    content = os.linesep.join([s for s in content.splitlines() if s.strip()])
    return content

def raw_file(path: str) -> Tuple[str, int]:
    """Returns the raw file content and token count."""
    try:
        content = Path(path).read_text(encoding="utf-8")
        tokens = tokenizer.count(content)
        return content, tokens
    except Exception as e:
        return f"# could not read file: {e}", 0

def optimize_file(path: str) -> Tuple[str, int]:
    """
    Main fallback chain for context optimization.
    Returns (optimized_content, tokens_used).
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"# could not read file: {e}", 0

    # 1. tree-sitter AST
    try:
        skel = _tree_sitter_skeleton(path, content)
        return skel, tokenizer.count(skel)
    except Exception:
        pass

    # 2. stdlib ast (Python only)
    if path.endswith(".py"):
        try:
            skel = _ast_skeleton(content)
            return skel, tokenizer.count(skel)
        except Exception:
            pass

    # 3. Regex comment strip
    try:
        stripped = _strip_comments(content)
        return stripped, tokenizer.count(stripped)
    except Exception:
        pass

    # 4. Raw file read
    return raw_file(path)

def extract_function(path: str, func_name: str) -> Tuple[str, int]:
    """
    Extracts a single function body by name.
    Returns (function_content, tokens_used).
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"# could not read file: {e}", 0

    # 1. tree-sitter AST
    try:
        func_content = _tree_sitter_extract_function(path, content, func_name)
        return func_content, tokenizer.count(func_content)
    except Exception:
        pass

    # 2. stdlib ast (Python only)
    if path.endswith(".py"):
        try:
            func_content = _ast_extract_function(content, func_name)
            return func_content, tokenizer.count(func_content)
        except Exception:
            pass
            
    # 3. Fallback to raw file if not found, with error message
    return f"# Function '{func_name}' could not be extracted accurately. Use raw read or check name.", 0

import os
