"""Builtin logger adapters."""
from __future__ import annotations
import pathlib
from typing import Any, Dict, Iterable
from . import register_adapter


class JsonlLoggerAdapter:
    key = "jsonl"

    def paths(self, cfg: Dict[str, Any]) -> Iterable[pathlib.Path]:
        reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/"))
        return [reports_dir / "debug.log.jsonl"]


register_adapter("logger", "jsonl", JsonlLoggerAdapter())
