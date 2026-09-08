"""
ICT Agent MCP Server — entry point for running the agent as an MCP server.

This script is the public interface for MCP-compatible clients (Claude Desktop,
Cursor, etc.) to access the ICT agent's analysis tools.

Usage:
    # Stdio mode (default — for Claude Desktop / Cursor)
    python -m ict_agent.mcp_server

    # Streamable HTTP mode
    MCP_TRANSPORT=http python -m ict_agent.mcp_server

    # Custom host/port
    MCP_TRANSPORT=http MCP_HOST=0.0.0.0 MCP_PORT=9000 python -m ict_agent.mcp_server

Configuration (via environment variables):
    MCP_TRANSPORT   stdio | http  (default: stdio)
    MCP_HOST        bind address (default: 127.0.0.1)
    MCP_PORT        bind port   (default: 8000)

See .env.example for required API keys.
"""
import sys
import os

# Ensure the project root is on sys.path when run as `python -m ict_agent.mcp_server`
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from harness.mcp_bridge import main

if __name__ == "__main__":
    main()
