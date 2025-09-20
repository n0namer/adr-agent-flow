import json
import os
import pathlib
import re
import sys
from typing import Any, Dict

import yaml


def load_yaml_front_matter(md_path: str) -> Dict[str, Any]:
    text = pathlib.Path(md_path).read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def read_json(path: str, default=None):
    p = pathlib.Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(path: str, data: Any):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fail(msg: str):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str):
    print(f"OK: {msg}")
