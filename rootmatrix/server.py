import logging
from fastmcp import FastMCP

from rootmatrix.engine.budget import check_budget, record_usage, get_budget_status
from rootmatrix.engine.filter import optimize_file, raw_file, extract_function
from rootmatrix.engine.vector_store import search, upsert_files
from rootmatrix.engine.project_map import generate_map
from rootmatrix.engine.search import find_references_in_workspace

# Set up logging to avoid corrupting MCP STDIO
logging.basicConfig(level=logging.INFO, filename="rootmatrix-server.log",
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("RootMatrix Engine")

@mcp.tool()
def read_optimized_file(file_path: str) -> dict:
    """
    Returns a structurally optimized skeleton of a file.
    Use this to understand the structure without consuming excessive tokens.
    """
    budget = check_budget(file_path)
    if budget.get("blocked"):
        logger.warning(f"Budget blocked on read_optimized_file: {file_path}")
        return budget

    try:
        content, tokens = optimize_file(file_path)
        record_usage(tokens, file_path, source="read_optimized_file")
        return {
            "content": content,
            "tokens_used": tokens
        }
    except Exception as e:
        logger.error(f"Error in read_optimized_file: {e}")
        return {
            "error": str(e),
            "blocked": False
        }

@mcp.tool()
def read_raw_file(file_path: str) -> dict:
    """
    Returns the full, unoptimized content of a file.
    Use this when you specifically need the complete implementation details.
    """
    budget = check_budget(file_path)
    if budget.get("blocked"):
        logger.warning(f"Budget blocked on read_raw_file: {file_path}")
        return budget

    try:
        content, tokens = raw_file(file_path)
        record_usage(tokens, file_path, source="read_raw_file")
        return {
            "content": content,
            "tokens_used": tokens
        }
    except Exception as e:
        logger.error(f"Error in read_raw_file: {e}")
        return {
            "error": str(e),
            "blocked": False
        }

@mcp.tool()
def search_codebase(file_path: str, query: str, n_results: int = 5) -> dict:
    """
    Searches the local project vector DB for the given query.
    Note: file_path must be a path inside the project to resolve the correct DB.
    """
    budget = check_budget(file_path)
    if budget.get("blocked"):
        logger.warning(f"Budget blocked on search_codebase: {file_path}")
        return budget
        
    try:
        if n_results > 5:
            n_results = 5
            
        results = search(file_path, query, n_results)
        total_tokens = 0
        
        # Replace raw content with optimized content to save massive amounts of tokens
        for res in results:
            path = res.get("metadata", {}).get("path")
            if path:
                skel, t = optimize_file(path)
                res["content"] = skel
                total_tokens += t
            elif "content" in res and len(res["content"]) > 500:
                res["content"] = res["content"][:500] + "\n...[Content Truncated]"

        record_usage(total_tokens, file_path, source="search_codebase")
        
        return {
            "results": results,
            "tokens_used": total_tokens
        }
    except Exception as e:
        logger.error(f"Error in search_codebase: {e}")
        return {
            "error": str(e),
            "blocked": False
        }

@mcp.tool()
def index_file(file_path: str) -> dict:
    """
    Indexes the specified file into the project's vector DB for future searches.
    """
    try:
        content, tokens = raw_file(file_path)
        upsert_files(file_path, [{"path": file_path, "content": content}])
        return {"status": "success", "file": file_path, "tokens_used": tokens}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_project_map(dir_path: str = ".") -> dict:
    """
    Returns a tree structure of the workspace, excluding noise like node_modules and .git.
    Use this to understand the high-level layout of the project without opening files.
    """
    try:
        content = generate_map(dir_path)
        return {"content": content, "tokens_used": 0}
    except Exception as e:
        logger.error(f"Error in get_project_map: {e}")
        return {"error": str(e), "blocked": False}

@mcp.tool()
def read_function(file_path: str, function_name: str) -> dict:
    """
    Extracts and returns the full body of a specific function.
    Use this to get targeted implementation details and save context tokens.
    """
    budget = check_budget(file_path)
    if budget.get("blocked"):
        return budget

    try:
        content, tokens = extract_function(file_path, function_name)
        record_usage(tokens, file_path, source="read_function")
        return {
            "content": content,
            "tokens_used": tokens
        }
    except Exception as e:
        logger.error(f"Error in read_function: {e}")
        return {"error": str(e), "blocked": False}

@mcp.tool()
def find_references(dir_path: str, symbol_name: str) -> dict:
    """
    Searches for references to a symbol across the workspace and returns them.
    Useful for understanding where a function or class is used before modifying it.
    """
    # Just checking budget for general limits, even though this scans many files
    budget = check_budget(None)
    if budget.get("blocked"):
        return budget

    try:
        result = find_references_in_workspace(dir_path, symbol_name)
        record_usage(result.get("tokens_used", 0), dir_path, source="find_references")
        return result
    except Exception as e:
        logger.error(f"Error in find_references: {e}")
        return {"error": str(e), "blocked": False}

@mcp.tool()
def get_context_budget(file_path: str = None) -> dict:
    """
    Returns the current context token usage and remaining budget.
    Always check this before making massive file read requests.
    """
    try:
        status = get_budget_status(file_path)
        return {"status": status}
    except Exception as e:
        logger.error(f"Error in get_context_budget: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run()
