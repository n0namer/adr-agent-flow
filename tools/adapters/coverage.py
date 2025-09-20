"""Builtin coverage adapters."""
from __future__ import annotations
import json
import pathlib
from typing import Any, Dict
from . import register_adapter


class CoverageJsonAdapter:
    key = "coverage-json"

    def read(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        reports_dir = cfg.get("paths", {}).get("reports", "reports/")
        path = pathlib.Path(reports_dir) / "coverage.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))


register_adapter("coverage", "coverage-json", CoverageJsonAdapter())
