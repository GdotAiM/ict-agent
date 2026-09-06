"""
Code-generation chain for the ICT Agent.

Implements the exact Udacity use-case:

  1. Prompt → Outline of the script
       Gate 1: list format + read/process/write (or ICT equivalents)
  2. Prompt → Full Python code from the outline
       Gate 2: ast.parse() + import allow-list
  3. (on failure) Prompt → Refine with the exact error feedback
       Re-run Gate 2 up to GATE_MAX_RETRIES times

The generated scripts are intended for ICT workflows:
  - turn a session JSONL into a CSV / markdown trade journal
  - simple pandas scanners that look for the same confluence the agent uses
  - post-session analysis helpers

No market tools are called; this is a pure LLM + validation chain.
"""
from __future__ import annotations
import config
from harness.plugin import ModelAdapterPlugin
from harness.session_log import SessionLog
from agent.codegen_gates import (
    gate_outline, gate_code_syntax, extract_final_code, GateResult,
)


OUTLINE_PROMPT = """You are a careful programming assistant working inside an ICT
(Inner Circle Trader / Smart Money Concepts) trading agent.

Task:
{task}

Produce a simple step-by-step OUTLINE for a Python script that accomplishes
the task. Use a numbered or bulleted list. Cover the classic flow:

  1. Read / load the input
  2. Process / calculate / analyse
  3. Write / export the result

Do NOT write any Python code yet — only the outline.
Keep it short and practical. Prefer the standard library or pandas/numpy.
"""

CODE_PROMPT = """You are a careful programming assistant working inside an ICT
(Inner Circle Trader / Smart Money Concepts) trading agent.

Task:
{task}

Here is the approved outline:

{outline}

Write a complete, self-contained Python script that follows the outline.
Requirements:
- Use only standard library modules or pandas / numpy.
- Prefer the 'csv' and 'json' modules when possible; pandas is fine for heavier work.
- Include a short module docstring and a `if __name__ == "__main__":` block.
- Make file paths easy to change (constants or argparse).
- Do not invent external APIs or network calls.

Return the full script inside a single ```python ... ``` fence.
"""

REFINE_PROMPT = """You are a careful programming assistant.

The script you previously generated has a problem. Fix it.

Original task:
{task}

Outline that was approved:
{outline}

Previous code:
```python
{code}
```

Validation feedback:
{feedback}

Return the COMPLETE corrected script inside a single ```python ... ``` fence.
Do not apologise — just emit the fixed code.
"""


def _call_llm(adapter: ModelAdapterPlugin, system: str, user: str, session: SessionLog, tag: str) -> str:
    """Single non-tool LLM call; records the exchange in the session log."""
    messages = [{"role": "user", "content": user}]
    session.append("codegen_prompt", {"tag": tag, "text": user[:500]})
    response = adapter.call(system, tools=[], messages=messages)
    text = adapter.extract_text(response)
    session.append("codegen_response", {"tag": tag, "text": text[:2000]})
    return text


def _run_with_retries(
    adapter: ModelAdapterPlugin,
    system: str,
    build_prompt_fn,
    gate_fn,
    session: SessionLog,
    tag: str,
    max_retries: int,
) -> tuple[str, GateResult]:
    """
    Generic retry-with-feedback helper for a single step of the codegen chain.
    build_prompt_fn(attempt, previous_gate) -> user prompt string
    """
    text = ""
    gate = GateResult(passed=False, reason="not run")
    for attempt in range(max_retries + 1):
        user_prompt = build_prompt_fn(attempt, gate)
        text = _call_llm(adapter, system, user_prompt, session, f"{tag}_attempt{attempt}")
        gate = gate_fn(text)
        session.append("gate_check", {
            "stage": tag,
            "attempt": attempt,
            "passed": gate.passed,
            "reason": gate.reason,
            "extracted": {k: v for k, v in gate.extracted.items() if k != "code"},
        })
        if gate.passed:
            return text, gate
        if attempt < max_retries:
            session.append("gate_retry", {
                "stage": tag,
                "attempt": attempt + 1,
                "reason": gate.reason,
            })
    return text, gate


def run_codegen(
    adapter: ModelAdapterPlugin,
    task: str,
    session: SessionLog,
    system_prompt: str | None = None,
) -> str:
    """
    Full outline → code → (optional refine) chain.
    Returns a final narrative that includes the approved outline and the
    final Python code (or a clear failure message).
    """
    system = system_prompt or (
        "You are a precise Python programming assistant specialised in "
        "ICT / Smart Money Concepts trading workflows. "
        "You write clean, minimal, self-contained scripts."
    )
    max_retries = getattr(config, "GATE_MAX_RETRIES", 2)

    session.append("chain_start", {"mode": "codegen", "task": task})
    session.append("system_prompt", {"text": system})

    # ------------------------------------------------------------------
    # Step 1 — Outline
    # ------------------------------------------------------------------
    def outline_prompt(attempt: int, prev_gate: GateResult) -> str:
        base = OUTLINE_PROMPT.format(task=task)
        if attempt > 0 and prev_gate.feedback:
            return (
                base
                + "\n\n=== PREVIOUS OUTLINE FAILED VALIDATION ===\n"
                + prev_gate.feedback
                + "\n\nProduce a corrected outline only."
            )
        return base

    outline_text, outline_gate = _run_with_retries(
        adapter, system, outline_prompt, gate_outline, session, "outline", max_retries,
    )
    if not outline_gate.passed:
        final = (
            "CODEGEN CHAIN STOPPED at Outline step after retries.\n"
            f"Reason: {outline_gate.reason}\n\n"
            f"Last outline attempt:\n{outline_text}"
        )
        session.append("final_narrative", {"text": final, "stopped_at": "outline"})
        return final

    # ------------------------------------------------------------------
    # Step 2 — Code generation
    # ------------------------------------------------------------------
    def code_prompt(attempt: int, prev_gate: GateResult) -> str:
        if attempt == 0:
            return CODE_PROMPT.format(task=task, outline=outline_text)
        # refinement
        prev_code = extract_final_code(prev_gate.extracted.get("code", "") or "")
        # On first failure we may not have stored code yet; pull from last text
        if not prev_code:
            prev_code = extract_final_code(outline_text)  # unlikely
        return REFINE_PROMPT.format(
            task=task,
            outline=outline_text,
            code=prev_code or "(no code extracted)",
            feedback=prev_gate.feedback or prev_gate.reason,
        )

    # We need a slightly custom loop for code because the refine prompt
    # needs the previous *code*, not just the gate feedback.
    code_text = ""
    code_gate = GateResult(passed=False, reason="not run")
    for attempt in range(max_retries + 1):
        if attempt == 0:
            user_prompt = CODE_PROMPT.format(task=task, outline=outline_text)
        else:
            prev_code = code_gate.extracted.get("code") or extract_final_code(code_text)
            user_prompt = REFINE_PROMPT.format(
                task=task,
                outline=outline_text,
                code=prev_code or code_text,
                feedback=code_gate.feedback or code_gate.reason,
            )
            session.append("gate_retry", {
                "stage": "code",
                "attempt": attempt,
                "reason": code_gate.reason,
            })

        code_text = _call_llm(adapter, system, user_prompt, session, f"code_attempt{attempt}")
        code_gate = gate_code_syntax(code_text)
        session.append("gate_check", {
            "stage": "code",
            "attempt": attempt,
            "passed": code_gate.passed,
            "reason": code_gate.reason,
            "extracted": {k: v for k, v in code_gate.extracted.items() if k != "code"},
        })
        if code_gate.passed:
            break

    if not code_gate.passed:
        final = (
            "CODEGEN CHAIN STOPPED at Code step after retries.\n"
            f"Reason: {code_gate.reason}\n\n"
            f"Approved outline:\n{outline_text}\n\n"
            f"Last code attempt:\n{code_text}"
        )
        session.append("final_narrative", {"text": final, "stopped_at": "code"})
        return final

    # ------------------------------------------------------------------
    # Success
    # ------------------------------------------------------------------
    final_code = code_gate.extracted.get("code") or extract_final_code(code_text)
    final = (
        "=== ICT CODEGEN CHAIN COMPLETE ===\n\n"
        f"TASK:\n{task}\n\n"
        f"OUTLINE:\n{outline_text}\n\n"
        f"PYTHON SCRIPT:\n```python\n{final_code}\n```\n"
    )
    session.append("final_narrative", {"text": final, "stopped_at": None})
    session.append("codegen_result", {"code": final_code})
    session.append("chain_end", {"mode": "codegen", "success": True})
    return final
