"""Builtin security adapters."""
from __future__ import annotations
import json
import pathlib
from typing import Any, Dict
from . import register_adapter


class SecurityJsonAdapter:
    key = "json"

    def read(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        reports_dir = cfg.get("paths", {}).get("reports", "reports/")
        path = pathlib.Path(reports_dir) / "security.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))


register_adapter("security", "json", SecurityJsonAdapter())
