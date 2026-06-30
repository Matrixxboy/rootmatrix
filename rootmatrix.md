# RootMatrix 🧠

**Universal token optimization, intelligent context management, and codebase navigation for AI IDEs and MCP servers.**

RootMatrix (formerly Context-Gate) is a Model Context Protocol (MCP) server that acts as a "Second Brain" for AI agents (Cursor, Windsurf, Trae, Claude Code). It intercepts file read requests and enforces a strict progressive context strategy, forcing the AI to navigate codebases surgically instead of blindly reading massive raw files.

This prevents context window exhaustion, drastically speeds up AI generation, and eliminates hallucination caused by context noise.

---

## 🚀 Installation

Install the package via pip:

```bash
pip install rootmatrix
```

---

## 💻 Quick Start & IDE Integration

RootMatrix integrates seamlessly into your favorite AI IDEs with a single command. 

Navigate to your project directory and run:

```bash
# 1. Initialize the project context constraints
rootmatrix init-project

# 2. Inject the RootMatrix MCP Server into your IDE
rootmatrix init --ide cursor    # Or: windsurf, trae, claude-desktop
```

Once you restart your IDE, your AI agent will automatically have access to all RootMatrix optimization tools.

---

## 🛠️ Key Functionality & MCP Tools

When connected, AI agents automatically use these surgical tools instead of naive file reads:

- **`get_project_map`**: Generates a structural tree representation of the workspace, automatically filtering out noise (`node_modules`, `venv`, etc.).
- **`read_optimized_file`**: The default file inspection tool. Uses AST (Tree-sitter and Python native) to strip out inner implementation logic, leaving only imports, classes, signatures, and docstrings. *(Slashes a 4k-token file down to ~400 tokens).*
- **`read_function`**: Surgically extracts and returns only the code body of a specific function, keeping the rest of the file out of context.
- **`search_codebase`**: Local semantic RAG search powered by ChromaDB. Helps the AI find exact snippets using natural language.
- **`find_references`**: Locates global occurrences of a specific function or class across the workspace to map dependencies safely.
- **`get_context_budget`**: Enforces a strict daily token limit.

---

## 🔗 Manual MCP Integration

If you want to manually configure the MCP server for an IDE or AI agent instead of using the CLI, you can add the following configuration to your client's MCP settings file (e.g., `mcp.json` or `cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "rootmatrix": {
      "command": "python",
      "args": ["-m", "rootmatrix.server"]
    }
  }
}
```

Ensure that the Python environment where `rootmatrix` is installed is accessible in your system's PATH, or provide the absolute path to your Python executable in the `"command"` field.

---

## ⚙️ Requirements
- Python 3.10+

## 📄 License
This project is licensed under the MIT License.
