"""Base gate definitions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import os
import pathlib
import subprocess


@dataclass
class GateResult:
    ok: bool
    miss: List[str]
    artifact: Optional[str] = None


class Gate:
    key: str = "base"
    title: str = "Base Gate"

    def run(self, cfg: Dict[str, Any]) -> GateResult:  # pragma: no cover - interface
        raise NotImplementedError

    def run_cmd(self, cmd: str, cwd: Optional[str] = None) -> int:
        print(f"[gate:{self.key}] $ {cmd}")
        return subprocess.call(cmd, shell=True, cwd=cwd or os.getcwd())

    def read_json(self, path: str) -> Dict[str, Any]:
        p = pathlib.Path(path)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
