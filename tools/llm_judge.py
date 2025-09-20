"""LLM judge registry and helpers."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
from ext_registry import judges


class NoopJudge:
    key = "none"

    def judge(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return payload


def register_builtin() -> None:
    if not judges.has("none"):
        judges.register("none", NoopJudge())


def _provider_from_cfg(cfg: Optional[Dict[str, Any]]) -> Optional[str]:
    if not cfg:
        return None
    llm_cfg = cfg.get("llm_judge", {}) or {}
    provider = llm_cfg.get("provider")
    if provider:
        return str(provider).lower()
    return None


def judge(name: str, payload: Dict[str, Any], cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Route payload through configured LLM judge."""
    register_builtin()
    provider = _provider_from_cfg(cfg) or os.getenv("LLM_JUDGE", "none").lower() or "none"
    if judges.has(provider):
        return judges.get(provider).judge(name, payload)
    # fallback: if env requested unknown provider keep payload intact
    return payload
