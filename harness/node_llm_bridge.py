"""
Node.js LLM Bridge — works around Python SSL issues on this machine.

Node.js can reach external APIs fine; Python's SSL cert store is broken.
This module calls node scripts to make LLM requests instead of using
Python's anthropic/openai SDKs directly.
"""
import json
import subprocess
import tempfile
import os
from pathlib import Path


def _make_node_call(model: str, messages: list, tools: list | None, max_tokens: int = 2000) -> dict:
    """Call a Node.js script that makes the LLM request and returns structured output."""
    # Get API key from environment — pass it in the JSON so Node doesn't need
    # dotenv (it can't load .env files itself). Falls back to empty string.
    import os as _os
    api_key = _os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or len(api_key) < 10:
        api_key = _os.getenv("OPENAI_API_KEY", "")
    if not api_key or len(api_key) < 10:
        api_key = _os.getenv("OPENROUTER_API_KEY", "")

    payload = {"model": model, "messages": messages, "tools": tools, "max_tokens": max_tokens}
    if api_key and len(api_key) >= 10:
        payload["api_key"] = api_key

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as mf:
        json.dump(payload, mf)
        input_file = mf.name
    
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).parent / "node_llm_call.cjs"), input_file],
            capture_output=True, text=True, timeout=int(os.environ.get('LLM_TIMEOUT_SEC', '180'))*1000/1000,
            encoding='utf-8', errors='replace',
        )
        if result.returncode != 0:
            return {"error": result.stderr[:500]}
        return json.loads(result.stdout.strip())
    finally:
        os.unlink(input_file)


class NodeLlmAdapter:
    """Adapter that uses Node.js for all LLM calls to avoid Python SSL issues."""
    
    def __init__(self, provider: str = "groq", model: str = "llama-3.1-8b-instant"):
        self.name = f"node:{provider}:{model}"
        self.provider = provider
        self.model = model
    
    def call(self, system: str, tools: list, messages: list) -> dict:
        full_messages = [{"role": "system", "content": system}] + messages
        result = _make_node_call(
            model=self.model,
            messages=full_messages,
            tools=tools,
            max_tokens=2000
        )
        return result
    
    def extract_text(self, response: dict) -> str:
        return response.get("text", "")
    
    def extract_tool_calls(self, response: dict) -> list:
        return response.get("tool_calls", [])
    
    def is_done(self, response: dict) -> bool:
        return not response.get("tool_calls")
    
    def to_assistant_message(self, response: dict) -> dict:
        return {"role": "assistant", "content": response.get("text", "")}
    
    def to_tool_result_message(self, results: list) -> dict:
        # Gemini requires tool_call_id in the message
        if results:
            return {
                "role": "tool",
                "tool_call_id": results[0].get("tool_use_id", "default"),
                "content": json.dumps(results[0]["content"], default=str)
            }
        return {"role": "tool", "content": ""}


def make_node_adapter(provider: str = "groq", model: str = "llama-3.1-8b-instant"):
    return NodeLlmAdapter(provider, model)
