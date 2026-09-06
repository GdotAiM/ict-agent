"""
Gate checks for the ICT code-generation chain.

Follows the Udacity "Data Analysis Script Generation" use-case exactly:

  Gate 1 (Outline)  – format + content: must look like a step list and
                      contain the key verbs read / process / write
                      (or ICT equivalents).

  Gate 2 (Code)     – logic: Python's ast.parse() must succeed.
                      Optional import allow-list so the model cannot
                      pull in arbitrary network / os libraries.

On failure the codegen loop retries the same step with the exact error
message injected back into the prompt.
"""
from __future__ import annotations
import ast
import re
from dataclasses import dataclass, field


@dataclass
class GateResult:
    passed: bool
    reason: str
    extracted: dict = field(default_factory=dict)
    feedback: str = ""


# ---------------------------------------------------------------------------
# Outline gate (format + content)
# ---------------------------------------------------------------------------

_OUTLINE_VERBS = [
    "read", "load", "open", "parse",
    "process", "calculate", "compute", "analyse", "analyze", "extract",
    "write", "save", "export", "output", "dump",
]

# ICT-flavoured extras that also count as valid process steps
_ICT_VERBS = [
    "structure", "liquidity", "fvg", "order block", "bias", "confluence",
    "session", "journal", "sweep", "premium", "discount",
]


def gate_outline(text: str) -> GateResult:
    """
    Check that the outline is a recognisable list of steps and mentions
    the classic read → process → write flow (or ICT equivalents).
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Count lines that look like list items
    list_items = [
        ln for ln in lines
        if re.match(r"^(\d+[\.\)]\s+|[-*•]\s+)", ln)
    ]
    has_list = len(list_items) >= 2

    lower = text.lower()
    has_read = any(v in lower for v in ("read", "load", "open", "parse", "session"))
    has_process = any(v in lower for v in (
        "process", "calculate", "compute", "analyse", "analyze",
        "extract", "structure", "liquidity", "confluence", "journal",
    ))
    has_write = any(v in lower for v in ("write", "save", "export", "output", "dump", "csv", "markdown"))

    extracted = {
        "list_item_count": len(list_items),
        "has_read": has_read,
        "has_process": has_process,
        "has_write": has_write,
    }

    missing = []
    if not has_list:
        missing.append("numbered or bulleted step list")
    if not has_read:
        missing.append("a 'read/load' step")
    if not has_process:
        missing.append("a 'process/calculate/analyse' step")
    if not has_write:
        missing.append("a 'write/save/export' step")

    if missing:
        feedback = (
            "Outline gate failed. Produce a clear numbered or bulleted list of "
            "high-level steps that covers:\n"
            "  1. Reading / loading the input (CSV, session JSONL, candles, …)\n"
            "  2. Processing / calculating / analysing\n"
            "  3. Writing / exporting the result\n\n"
            f"Missing: {', '.join(missing)}.\n"
            "Do not write any Python code yet — only the outline."
        )
        return GateResult(
            passed=False,
            reason=f"Outline gate failed — missing: {', '.join(missing)}",
            extracted=extracted,
            feedback=feedback,
        )

    return GateResult(
        passed=True,
        reason=f"Outline gate passed ({len(list_items)} list items, read/process/write present).",
        extracted=extracted,
    )


# ---------------------------------------------------------------------------
# Code syntax gate (ast + optional import allow-list)
# ---------------------------------------------------------------------------

# Libraries the generated ICT helper scripts are allowed to import.
# Keep this tight; expand deliberately.
_ALLOWED_IMPORTS = {
    "csv", "json", "statistics", "math", "datetime", "pathlib", "os",
    "sys", "re", "collections", "typing", "dataclasses",
    "pandas", "numpy",
    # stdlib that often appears in journal scripts
    "argparse", "io", "textwrap", "pprint",
}


def _extract_code_block(text: str) -> str:
    """Pull the first fenced Python block, or the whole text if none found."""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # fallback: strip common leading prose
    lines = text.splitlines()
    code_lines = []
    in_code = False
    for ln in lines:
        if ln.strip().startswith(("import ", "from ", "def ", "class ", "#")):
            in_code = True
        if in_code:
            code_lines.append(ln)
    return "\n".join(code_lines).strip() if code_lines else text.strip()


def _check_imports(tree: ast.AST) -> list[str]:
    """Return list of disallowed top-level module names."""
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in _ALLOWED_IMPORTS:
                    bad.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in _ALLOWED_IMPORTS:
                    bad.append(node.module)
    return bad


def gate_code_syntax(text: str) -> GateResult:
    """
    Validate that the generated code is syntactically correct Python
    and only imports from the allow-list.
    """
    code = _extract_code_block(text)
    extracted = {"code_length": len(code), "code_preview": code[:200]}

    if not code or len(code) < 20:
        feedback = (
            "Code gate failed: no usable Python code found. "
            "Wrap the complete script in a ```python ... ``` fence and try again."
        )
        return GateResult(
            passed=False,
            reason="No Python code block detected.",
            extracted=extracted,
            feedback=feedback,
        )

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        feedback = (
            "The following Python code contains a syntax error.\n\n"
            f"Code:\n```python\n{code}\n```\n\n"
            f"Error: {e.__class__.__name__}: {e.msg} "
            f"(line {e.lineno}, offset {e.offset})\n\n"
            "Please correct the code and return the full fixed script "
            "inside a ```python fence."
        )
        return GateResult(
            passed=False,
            reason=f"SyntaxError: {e.msg} (line {e.lineno})",
            extracted={**extracted, "syntax_error": str(e)},
            feedback=feedback,
        )

    bad_imports = _check_imports(tree)
    if bad_imports:
        feedback = (
            "Code gate failed: disallowed imports detected.\n"
            f"Forbidden modules: {', '.join(sorted(set(bad_imports)))}\n"
            f"Allowed modules: {', '.join(sorted(_ALLOWED_IMPORTS))}\n\n"
            "Rewrite the script using only the allowed libraries and "
            "return the full fixed script inside a ```python fence."
        )
        return GateResult(
            passed=False,
            reason=f"Disallowed imports: {bad_imports}",
            extracted={**extracted, "bad_imports": bad_imports},
            feedback=feedback,
        )

    return GateResult(
        passed=True,
        reason="Code syntax + import allow-list passed.",
        extracted={**extracted, "code": code},
    )


def extract_final_code(text: str) -> str:
    """Public helper: return the cleaned code block from a passed stage."""
    return _extract_code_block(text)
