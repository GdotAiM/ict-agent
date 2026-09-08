"""
MCP Bridge — exposes the ICT agent's PluginKernel as an MCP server.

Maps existing ToolPlugin entries to FastMCP tools so the agent can be called
from any MCP-compatible client (Claude Desktop, Cursor, another agent, etc.)
without changing the tool implementations.

Usage:
    python -m harness.mcp_bridge          # stdio mode (default)
    MCP_TRANSPORT=http python -m harness.mcp_bridge  # Streamable HTTP mode
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import config
from pathlib import Path


# ---------------------------------------------------------------------------
# Import fast-mcp only when needed
# ---------------------------------------------------------------------------

def _import_fastmcp():
    from mcp.server.fastmcp import FastMCP
    return FastMCP


def _build_handler(plugin_name: str, plugin_obj) -> callable:
    """
    Build a FastMCP-compatible async handler for one ToolPlugin.
    Uses exec() to dynamically create a function with typed params matching
    the plugin's input_schema so FastMCP's arg validation passes.
    """
    schema = plugin_obj.input_schema
    props = schema.get("properties", {})
    required = set(schema.get("required", []))

    if not props:
        async def _handler():
            try:
                result = plugin_obj.handler({}, None)
                return json.dumps(result, default=str, ensure_ascii=False) if isinstance(result, dict) else str(result)
            except Exception as exc:
                return json.dumps({"error": str(exc)}, ensure_ascii=False)
        _handler.__name__ = f"_mcp_{plugin_name}"
        return _handler

    param_lines = []
    for pname in props:
        ptype = props[pname].get("type", "str")
        type_map = {"string": "str", "number": "float", "integer": "int", "boolean": "bool"}
        hint = type_map.get(ptype, "str")
        default = "" if pname in required else "=None"
        param_lines.append(f"    {pname}: {hint}{default}")
    params_str = ",\n".join(param_lines)

    # Import RunContext here so we can instantiate it for tool handlers
    func_body = f'''
async def _handler({params_str}):
    from harness.context import RunContext
    kwargs = {{k: v for k, v in locals().items() if v is not None}}
    ctx = RunContext()
    try:
        result = plugin_obj.handler(kwargs, ctx)
        return json.dumps(result, default=str, ensure_ascii=False) if isinstance(result, dict) else str(result)
    except Exception as exc:
        return json.dumps({{"error": str(exc)}}, ensure_ascii=False)
_handler.__name__ = "_mcp_{plugin_name}"
_handler.__doc__ = "{plugin_name}: {plugin_obj.description}"
'''
    namespace = {"json": json, "plugin_obj": plugin_obj}
    exec(func_body, namespace)
    return namespace["_handler"]


def _build_bridge(mcp) -> list[str]:
    """
    Dynamically register every ToolPlugin as an MCP tool.
    Returns list of registered tool names.
    """
    from harness.kernel import build_default_kernel
    kernel = build_default_kernel()
    tool_names = []

    for plugin in kernel.tools.values():
        name = plugin.name
        desc = plugin.description
        handler = _build_handler(name, plugin)
        handler.__name__ = f"_mcp_{name}"
        handler.__doc__ = f"MCP: {name} — {desc}"

        decorated = mcp.tool(name=name)(handler)
        tool_names.append(name)

    return tool_names


def run_stdio() -> None:
    """Run the ICT agent as an MCP server over stdin/stdout."""
    FastMCP = _import_fastmcp()
    mcp = FastMCP("ict-agent")
    names = _build_bridge(mcp)
    print(f"[mcp] Registered {len(names)} tools, starting stdio...", file=sys.stderr, flush=True)
    mcp.run_stdio()


def run_streamable_http(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the ICT agent as an MCP server over Streamable HTTP."""
    import uvicorn
    FastMCP = _import_fastmcp()
    mcp = FastMCP("ict-agent")
    names = _build_bridge(mcp)
    app = mcp.streamable_http_app()
    print(f"[mcp] MCP Streamable HTTP at http://{host}:{port}/mcp  ({len(names)} tools)",
          file=sys.stderr, flush=True)
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main():
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ("http", "streamable_http"):
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        run_streamable_http(host=host, port=port)
    else:
        run_stdio()


if __name__ == "__main__":
    main()
