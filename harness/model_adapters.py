"""
Model adapters — "Agent = Model + Harness". Everything above this file
(the loop, the kernel, every tool) is provider-agnostic. Today only
AnthropicAdapter is wired up; DeepSeekAdapter below is a stub showing
exactly how little you'd need to add DeepSeek-V4-Flash as a second,
much-cheaper option for high-frequency scanning while keeping Claude for
the trades you actually act on.
"""
import json
import anthropic
from harness.plugin import ModelAdapterPlugin
import config


def make_anthropic_adapter(api_key: str, model: str) -> ModelAdapterPlugin:
    import httpx2
    http = httpx2.Client(verify=False)  # work around broken certifi on Python 3.14 / Avast MITM
    client = anthropic.Anthropic(api_key=api_key, http_client=http)

    def call(system: str, tools: list, messages: list):
        response = client.messages.create(
            model=model, max_tokens=2000, system=system,
            tools=tools, messages=messages,
        )
        text_parts = []
        tool_calls = []
        for block in response.content:
            if hasattr(block, 'type'):
                if block.type == 'text':
                    text_parts.append(block.text)
                elif block.type == 'tool_use':
                    tool_calls.append({
                        'id': block.id,
                        'name': block.name,
                        'input': block.input
                    })
        usage = response.usage
        return {
            'text': '\n'.join(text_parts),
            'tool_calls': tool_calls,
            'done': response.stop_reason != 'tool_use',
            'usage': {
                'input_tokens': int(getattr(usage, 'input_tokens', 0)),
                'output_tokens': int(getattr(usage, 'output_tokens', 0)),
            }
        }

    def extract_text(response) -> str:
        return response.get('text', '')

    def extract_tool_calls(response) -> list:
        return response.get('tool_calls', [])

    def is_done(response) -> bool:
        return response.get('done', True)

    def to_assistant_message(response) -> dict:
        return {"role": "assistant", "content": response.get('text', '')}

    def to_tool_result_message(results: list) -> dict:
        return {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": r["tool_use_id"],
                 "content": json.dumps(r["content"], default=str)}
                for r in results
            ],
        }

    return ModelAdapterPlugin(
        name=f"anthropic:{model}", call=call, extract_text=extract_text,
        extract_tool_calls=extract_tool_calls, is_done=is_done,
        to_assistant_message=to_assistant_message,
        to_tool_result_message=to_tool_result_message,
    )

def make_deepseek_adapter(api_key: str, model: str = "deepseek-v4-flash") -> ModelAdapterPlugin:
    """
    STUB — not wired into config.py by default. DeepSeek's API is OpenAI
    tool-calling-compatible, so this is the shape it would take (using the
    `openai` client pointed at DeepSeek's base_url). Useful later for
    running a cheap, high-frequency version of this agent (e.g. scanning
    the full watchlist every few minutes) and reserving the Anthropic
    adapter for the smaller number of cycles that actually reach a trade
    decision.
    """
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def to_openai_tools(tools: list) -> list:
        return [{"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": t["input_schema"]}} for t in tools]

    def call(system: str, tools: list, messages: list):
        oai_messages = [{"role": "system", "content": system}] + messages
        return client.chat.completions.create(
            model=model, messages=oai_messages, tools=to_openai_tools(tools),
            temperature=config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
            frequency_penalty=config.LLM_FREQUENCY_PENALTY,
        )

    def extract_text(response) -> str:
        return response.choices[0].message.content or ""

    def extract_tool_calls(response) -> list:
        msg = response.choices[0].message
        if not msg.tool_calls:
            return []
        return [{"id": tc.id, "name": tc.function.name,
                  "input": json.loads(tc.function.arguments)}
                for tc in msg.tool_calls]

    def is_done(response) -> bool:
        return response.choices[0].finish_reason != "tool_calls"

    def to_assistant_message(response) -> dict:
        return response.choices[0].message.model_dump()

    def to_tool_result_message(results: list) -> dict:
        # OpenAI-style: one message per tool result, not batched — caller
        # (loop.py) handles this via to_tool_result_messages if needed.
        return {"role": "tool", "tool_call_id": results[0]["tool_use_id"],
                "content": json.dumps(results[0]["content"], default=str)}

    return ModelAdapterPlugin(
        name=f"deepseek:{model}", call=call, extract_text=extract_text,
        extract_tool_calls=extract_tool_calls, is_done=is_done,
        to_assistant_message=to_assistant_message,
        to_tool_result_message=to_tool_result_message,
    )


def make_openrouter_adapter(api_key: str, model: str) -> ModelAdapterPlugin:
    """Generic OpenAI-compatible adapter for OpenRouter and any compatible proxy."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def to_openai_tools(tools: list) -> list:
        return [{"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": t["input_schema"]}} for t in tools]

    def call(system: str, tools: list, messages: list):
        oai_messages = [{"role": "system", "content": system}] + messages
        result = client.chat.completions.create(
            model=model, messages=oai_messages, tools=to_openai_tools(tools),
            temperature=config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
            frequency_penalty=config.LLM_FREQUENCY_PENALTY,
        )
        usage = result.usage
        return {
            '_raw': result,
            'usage': {
                'input_tokens': int(getattr(usage, 'prompt_tokens', 0)),
                'output_tokens': int(getattr(usage, 'completion_tokens', 0)),
            }
        }

    def extract_text(response) -> str:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.content or ""

    def extract_tool_calls(response) -> list:
        raw = getattr(response, '_raw', response)
        msg = raw.choices[0].message
        if not msg.tool_calls:
            return []
        out = []
        for tc in msg.tool_calls:
            try:
                inp = json.loads(tc.function.arguments)
            except Exception:
                inp = {"raw": tc.function.arguments}
            out.append({"id": tc.id, "name": tc.function.name, "input": inp})
        return out

    def is_done(response) -> bool:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].finish_reason != "tool_calls"

    def to_assistant_message(response) -> dict:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.model_dump()

    def to_tool_result_message(results: list) -> dict:
        return {"role": "tool", "tool_call_id": results[0]["tool_use_id"],
                "content": json.dumps(results[0]["content"], default=str)}

    return ModelAdapterPlugin(
        name=f"openrouter:{model}", call=call, extract_text=extract_text,
        extract_tool_calls=extract_tool_calls, is_done=is_done,
        to_assistant_message=to_assistant_message,
        to_tool_result_message=to_tool_result_message,
    )


def make_cerebras_adapter(api_key: str, model: str) -> ModelAdapterPlugin:
    """Cerebras Cloud API adapter (free tier: 1M tokens/day)."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.cerebras.ai/v1")

    def to_openai_tools(tools: list) -> list:
        return [{"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": t["input_schema"]}} for t in tools]

    def call(system: str, tools: list, messages: list):
        oai_messages = [{"role": "system", "content": system}] + messages
        result = client.chat.completions.create(
            model=model, messages=oai_messages, tools=to_openai_tools(tools),
            temperature=config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
            frequency_penalty=config.LLM_FREQUENCY_PENALTY,
        )
        usage = result.usage
        return {
            '_raw': result,
            'usage': {
                'input_tokens': int(getattr(usage, 'prompt_tokens', 0)),
                'output_tokens': int(getattr(usage, 'completion_tokens', 0)),
            }
        }

    def extract_text(response) -> str:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.content or ""

    def extract_tool_calls(response) -> list:
        raw = getattr(response, '_raw', response)
        msg = raw.choices[0].message
        if not msg.tool_calls:
            return []
        out = []
        for tc in msg.tool_calls:
            try:
                inp = json.loads(tc.function.arguments)
            except Exception:
                inp = {"raw": tc.function.arguments}
            out.append({"id": tc.id, "name": tc.function.name, "input": inp})
        return out

    def is_done(response) -> bool:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].finish_reason != "tool_calls"

    def to_assistant_message(response) -> dict:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.model_dump()

    def to_tool_result_message(results: list) -> dict:
        return {"role": "tool", "tool_call_id": results[0]["tool_use_id"],
                "content": json.dumps(results[0]["content"], default=str)}

    return ModelAdapterPlugin(
        name=f"cerebras:{model}", call=call, extract_text=extract_text,
        extract_tool_calls=extract_tool_calls, is_done=is_done,
        to_assistant_message=to_assistant_message,
        to_tool_result_message=to_tool_result_message,
    )


def make_groq_adapter(api_key: str, model: str) -> ModelAdapterPlugin:
    """Groq Cloud API adapter (free tier: 14,400 req/day)."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    def to_openai_tools(tools: list) -> list:
        return [{"type": "function", "function": {
            "name": t["name"], "description": t["description"],
            "parameters": t["input_schema"]}} for t in tools]

    def call(system: str, tools: list, messages: list):
        oai_messages = [{"role": "system", "content": system}] + messages
        result = client.chat.completions.create(
            model=model, messages=oai_messages, tools=to_openai_tools(tools),
            temperature=config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
            frequency_penalty=config.LLM_FREQUENCY_PENALTY,
        )
        usage = result.usage
        return {
            '_raw': result,
            'usage': {
                'input_tokens': int(getattr(usage, 'prompt_tokens', 0)),
                'output_tokens': int(getattr(usage, 'completion_tokens', 0)),
            }
        }

    def extract_text(response) -> str:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.content or ""

    def extract_tool_calls(response) -> list:
        raw = getattr(response, '_raw', response)
        msg = raw.choices[0].message
        if not msg.tool_calls:
            return []
        out = []
        for tc in msg.tool_calls:
            try:
                inp = json.loads(tc.function.arguments)
            except Exception:
                inp = {"raw": tc.function.arguments}
            out.append({"id": tc.id, "name": tc.function.name, "input": inp})
        return out

    def is_done(response) -> bool:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].finish_reason != "tool_calls"

    def to_assistant_message(response) -> dict:
        raw = getattr(response, '_raw', response)
        return raw.choices[0].message.model_dump()

    def to_tool_result_message(results: list) -> dict:
        return {"role": "tool", "tool_call_id": results[0]["tool_use_id"],
                "content": json.dumps(results[0]["content"], default=str)}

    return ModelAdapterPlugin(
        name=f"groq:{model}", call=call, extract_text=extract_text,
        extract_tool_calls=extract_tool_calls, is_done=is_done,
        to_assistant_message=to_assistant_message,
        to_tool_result_message=to_tool_result_message,
    )
