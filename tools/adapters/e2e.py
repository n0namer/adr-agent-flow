"""Builtin e2e adapters."""
from __future__ import annotations
import json
import pathlib
from typing import Any, Dict
from . import register_adapter


class SimpleE2EAdapter:
    key = "json"

    def read(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/")) / "e2e"
        result: Dict[str, Any] = {}
        if not reports_dir.exists():
            return result
        for path in reports_dir.glob("*.json"):
            try:
                result[path.stem] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
        return result


register_adapter("e2e", "json", SimpleE2EAdapter())
