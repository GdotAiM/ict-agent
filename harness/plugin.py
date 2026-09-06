"""
Plugin primitives — everything the agent can do (a tool call, a model,
a memory read/write) is described as one of these, and nothing outside
harness/kernel.py needs to know how a given plugin is implemented.

This is the "spatial composability" half of the design: any tool below can
be mounted, replaced, or removed without touching the loop, the model
adapter, or any other tool.
"""
from dataclasses import dataclass
from typing import Callable, Any, Dict


@dataclass
class ToolPlugin:
    name: str
    description: str
    input_schema: Dict[str, Any]
    # handler(tool_input: dict, ctx: RunContext) -> dict
    handler: Callable[[dict, Any], Any]

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass
class ModelAdapterPlugin:
    """Wraps a specific LLM provider behind one call() signature, so the
    loop and the rest of the harness never import a provider SDK directly.
    Swap Claude for DeepSeek-V4-Flash (or anything else) by writing one of
    these — see harness/model_adapters.py."""
    name: str
    call: Callable[[str, list, list], Any]  # (system, tools, messages) -> raw response
    extract_text: Callable[[Any], str]
    extract_tool_calls: Callable[[Any], list]  # -> [{"id","name","input"}]
    is_done: Callable[[Any], bool]
    to_assistant_message: Callable[[Any], dict]
    to_tool_result_message: Callable[[list], dict]  # [{"tool_use_id","content"}] -> message
