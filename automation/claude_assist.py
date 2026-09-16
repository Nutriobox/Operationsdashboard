"""
Claude API assist — the ONLY place an LLM is allowed to touch this pipeline,
and it stays OFF the happy path.

daily_data.py runs entirely on deterministic Python. These helpers are called
only when something the deterministic code cannot handle happens:

  1. extract_number(html, what)   a Petpooja page changed and a parser can't
                                  find a value it expects -> ask Claude to read
                                  the number straight off the HTML so the run
                                  self-heals instead of hard-failing.
  2. explain_anomaly(context)     a validation gate fired (low sales, missing
                                  outlet, big day-over-day swing) -> a short
                                  plain-English note for the run log.
  3. reconcile_judgment(context)  morning POS-vs-export mismatch -> decide
                                  re-export vs accept, with a reason.

DORMANT UNTIL KEYED. If ANTHROPIC_API_KEY is absent (or the `anthropic` package
isn't installed), every function returns a benign "unavailable" result and the
caller falls back to its fixed rule. Nothing here ever raises into the pipeline.

Enable later by adding to automation/.env (or the repo .env.local):
    ANTHROPIC_API_KEY=sk-ant-...
optionally:
    CLAUDE_ASSIST_MODEL=claude-sonnet-5      (default)
    CLAUDE_ASSIST_MAXTOKENS=1024
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Key discovery — checks env, automation/.env, and the repo .env.local.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).parent


def _load_env_files() -> None:
    for candidate in (_ROOT / ".env", _ROOT.parent / ".env.local"):
        if not candidate.exists():
            continue
        try:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except Exception:
            pass


_load_env_files()

_MODEL = os.environ.get("CLAUDE_ASSIST_MODEL", "claude-sonnet-5")
_MAXTOK = int(os.environ.get("CLAUDE_ASSIST_MAXTOKENS", "1024"))


@dataclass
class AssistResult:
    ok: bool                 # did Claude actually answer?
    value: object = None     # parsed answer (number / dict / str)
    note: str = ""           # human-readable note for the run log
    used_api: bool = False   # True only if a real API call was made


def available() -> bool:
    """True only if a key is present AND the SDK imports."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except Exception:
        return False


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _ask(system: str, user: str) -> str | None:
    """One-shot call. Returns the text, or None on any failure (never raises)."""
    if not available():
        return None
    try:
        msg = _client().messages.create(
            model=_MODEL,
            max_tokens=_MAXTOK,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in msg.content if getattr(block, "type", "") == "text"
        ).strip()
    except Exception as e:  # noqa: BLE001
        # Assist must never take the pipeline down.
        return f"__ERROR__:{e}"


def _trim_html(html: str, needle: str | None = None, span: int = 6000) -> str:
    """Petpooja pages are huge; send Claude a focused slice, not the whole DOM."""
    if needle:
        i = html.lower().find(needle.lower())
        if i != -1:
            lo = max(0, i - span // 2)
            return html[lo: lo + span]
    return html[:span]


# ---------------------------------------------------------------------------
# 1. Self-heal a broken parser
# ---------------------------------------------------------------------------
def extract_number(html: str, what: str, needle: str | None = None) -> AssistResult:
    """
    Ask Claude to read one number off a page a deterministic parser failed on.
    `what`   e.g. "total number of KOT records" / "grand Total Sales value".
    `needle` optional anchor text to focus the HTML slice around.
    """
    if not available():
        return AssistResult(False, note="claude assist unavailable (no key)")

    snippet = _trim_html(html, needle)
    system = (
        "You extract a single numeric value from a fragment of restaurant POS "
        "HTML. Reply with ONLY a JSON object: {\"value\": <number or null>, "
        "\"reason\": \"<short>\"}. Use null if the value is genuinely absent."
    )
    user = f"Value wanted: {what}\n\nHTML fragment:\n{snippet}"
    raw = _ask(system, user)
    if not raw or raw.startswith("__ERROR__"):
        return AssistResult(False, note=f"assist call failed: {raw}")
    try:
        m = re.search(r"\{.*\}", raw, re.S)
        obj = json.loads(m.group(0)) if m else json.loads(raw)
        val = obj.get("value")
        if val is None:
            return AssistResult(False, note=f"claude found no value: {obj.get('reason','')}")
        return AssistResult(
            True, value=float(val), used_api=True,
            note=f"claude self-heal read {what} = {val} ({obj.get('reason','')})",
        )
    except Exception as e:  # noqa: BLE001
        return AssistResult(False, note=f"could not parse claude reply ({e}): {raw[:200]}")


# ---------------------------------------------------------------------------
# 2. Explain an anomaly for the run log
# ---------------------------------------------------------------------------
def explain_anomaly(context: dict) -> AssistResult:
    if not available():
        return AssistResult(False, note="")
    system = (
        "You are a terse operations analyst for a restaurant chain. Given the "
        "run metrics and the warnings that fired, write 1-3 sentences a manager "
        "can read, naming the most likely cause and whether it needs action. "
        "No preamble, no markdown."
    )
    raw = _ask(system, json.dumps(context, indent=2, default=str))
    if not raw or raw.startswith("__ERROR__"):
        return AssistResult(False, note="")
    return AssistResult(True, value=raw, note=raw, used_api=True)


# ---------------------------------------------------------------------------
# 3. Reconciliation judgment (morning POS vs export)
# ---------------------------------------------------------------------------
def reconcile_judgment(context: dict) -> AssistResult:
    """
    context: {pos_total, export_total, delta, threshold, pos_by_outlet,
              export_by_outlet, already_reexported}
    Returns value in {"reexport", "accept"}.
    """
    if not available():
        return AssistResult(False, note="")
    system = (
        "You decide whether a restaurant sales export should be re-pulled. "
        "The morning export can lag hours behind the POS dashboard. Reply ONLY "
        "with JSON: {\"decision\": \"reexport\"|\"accept\", \"reason\": \"<short>\"}. "
        "Prefer 'accept' if a re-export has already been done, or if the export "
        "EXCEEDS the POS total (dashboard widgets lag too)."
    )
    raw = _ask(system, json.dumps(context, indent=2, default=str))
    if not raw or raw.startswith("__ERROR__"):
        return AssistResult(False, note="")
    try:
        m = re.search(r"\{.*\}", raw, re.S)
        obj = json.loads(m.group(0)) if m else json.loads(raw)
        dec = obj.get("decision")
        if dec not in ("reexport", "accept"):
            return AssistResult(False, note="")
        return AssistResult(True, value=dec, used_api=True,
                            note=f"claude reconcile: {dec} ({obj.get('reason','')})")
    except Exception:  # noqa: BLE001
        return AssistResult(False, note="")


if __name__ == "__main__":
    print("claude assist available:", available(), "| model:", _MODEL)
