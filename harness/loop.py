"""
The loop — RUNTIME/ORCHESTRATION, generalized so it doesn't know it's
trading ICT setups. It only knows: system prompt in, tool-capable model
calls out, dispatch through the kernel, log every step, stop when the
model stops calling tools or the iteration cap is hit.

Everything ICT-specific lives in instructions.py (what to think) and
tools/ (what it can check/do) — this file would be identical for a
completely different agent.
"""
import config
from harness.kernel import PluginKernel
from harness.plugin import ModelAdapterPlugin
from harness.context import RunContext
from harness.session_log import SessionLog


def run(kernel: PluginKernel, adapter: ModelAdapterPlugin, system_prompt: str,
        user_message: str, session: SessionLog, ctx: RunContext = None) -> str:
    ctx = ctx or RunContext()
    tools = kernel.tool_schemas()
    messages = [{"role": "user", "content": user_message}]

    session.append("system_prompt", {"text": system_prompt})
    session.append("user_message", {"text": user_message})
    session.append("mounted_tools", {"names": kernel.list_tools(),
                                      "model_adapter": adapter.name})

    for step in range(config.MAX_TOOL_ITERATIONS):
        response = adapter.call(system_prompt, tools, messages)
        messages.append(adapter.to_assistant_message(response))

        text = adapter.extract_text(response)
        calls = adapter.extract_tool_calls(response)
        session.append("model_response", {"step": step, "text": text,
                                           "tool_calls": [c["name"] for c in calls]})

        if adapter.is_done(response):
            session.append("final_narrative", {"text": text})
            return text

        results = []
        for call in calls:
            session.append("tool_call", {"name": call["name"], "input": call["input"]})
            result = kernel.dispatch(call["name"], call["input"], ctx)
            session.append("tool_result", {"name": call["name"], "result": result})
            results.append({"tool_use_id": call["id"], "content": result})

        messages.append(adapter.to_tool_result_message(results))

    session.append("max_iterations_hit", {"limit": config.MAX_TOOL_ITERATIONS})
    return "Hit max tool iterations without a final answer."
