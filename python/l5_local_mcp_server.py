import os

import uvicorn
from mcp.server.fastmcp import FastMCP


# Minimal local MCP server used as a notebook-safe replacement for the broken npx example.
mcp = FastMCP("NotebookMathServer", stateless_http=True, json_response=True)


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


if __name__ == "__main__":
    port = int(os.environ.get("MCP_PORT", "8000"))
    uvicorn.run(mcp.streamable_http_app(), host="127.0.0.1", port=port, log_level="error")
