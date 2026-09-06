"""
Kernel — the one place that knows which plugins are mounted. Everything
else (the loop, main.py) talks to the kernel, never to a tool module
directly. This is what makes "add a Silver Bullet timing tool" or "swap the
data source" a one-line change at the bottom of this file instead of a
hunt through the codebase.

Deliberately much simpler than DeepSeek Harness's Cordis kernel (no
dependency graph, no hot-reload, no sandboxing) — but the same shape:
explicit mount points for tools and a model adapter, nothing hardcoded
into the loop itself.
"""
from harness.plugin import ToolPlugin, ModelAdapterPlugin


class PluginKernel:
    def __init__(self):
        self.tools: dict[str, ToolPlugin] = {}
        self.model_adapter: ModelAdapterPlugin | None = None

    # ---- mounting ----------------------------------------------------
    def mount_tool(self, plugin: ToolPlugin):
        if plugin.name in self.tools:
            raise ValueError(f"tool '{plugin.name}' already mounted")
        self.tools[plugin.name] = plugin

    def mount_tools(self, plugins: list[ToolPlugin]):
        for p in plugins:
            self.mount_tool(p)

    def mount_model_adapter(self, adapter: ModelAdapterPlugin):
        self.model_adapter = adapter

    def unmount_tool(self, name: str):
        self.tools.pop(name, None)

    # ---- introspection -------------------------------------------------
    def tool_schemas(self) -> list[dict]:
        return [p.schema() for p in self.tools.values()]

    def list_tools(self) -> list[str]:
        return sorted(self.tools.keys())

    # ---- dispatch --------------------------------------------------------
    def dispatch(self, name: str, tool_input: dict, ctx) -> dict:
        plugin = self.tools.get(name)
        if plugin is None:
            return {"error": f"unknown tool: {name}"}
        try:
            return plugin.handler(tool_input, ctx)
        except Exception as e:
            return {"error": str(e)}


def build_default_kernel() -> PluginKernel:
    """The mount list — this IS the agent's capability surface. Comment a
    line out to remove a tool; add a module + PLUGINS list to grant a new
    one. Nothing else in the codebase needs to change."""
    from tools import market_data, structure, liquidity, fvg, order_blocks, pd_arrays, kill_zones, execution, knowledge, economic_calendar
    from memory import store as memory_store

    kernel = PluginKernel()
    kernel.mount_tools(market_data.PLUGINS)
    kernel.mount_tools(structure.PLUGINS)
    kernel.mount_tools(liquidity.PLUGINS)
    kernel.mount_tools(fvg.PLUGINS)
    kernel.mount_tools(order_blocks.PLUGINS)
    kernel.mount_tools(pd_arrays.PLUGINS)
    kernel.mount_tools(kill_zones.PLUGINS)
    kernel.mount_tools(execution.PLUGINS)
    kernel.mount_tools(knowledge.PLUGINS)
    kernel.mount_tools(economic_calendar.PLUGINS)
    kernel.mount_tools(memory_store.PLUGINS)
    return kernel
