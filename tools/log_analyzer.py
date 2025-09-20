#!/usr/bin/env python
import argparse
import json
import pathlib
from typing import Any, Dict, List

from common import fail, load_yaml_front_matter, ok, write_json


def load_adr_specs(adr_dir: str) -> Dict[str, Dict[str, Any]]:
    specs: Dict[str, Dict[str, Any]] = {}
    for path in pathlib.Path(adr_dir).glob("ADR-*.md"):
        front_matter = load_yaml_front_matter(str(path))
        if front_matter:
            specs[front_matter["adr_id"]] = front_matter
    return specs


def iter_jsonl(path: str):
    file_path = pathlib.Path(path)
    if not file_path.exists():
        return
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def check_logs_against_adr(adr: Dict[str, Any], logs_path: str) -> Dict[str, Any]:
    missing: List[str] = []
    samples: List[Dict[str, Any]] = []
    log_requirements = (adr.get("observability_signals") or {}).get("logs") or []
    entries = list(iter_jsonl(logs_path) or [])
    if not entries and log_requirements:
        return {"pass": False, "miss": [f"logs file not found or empty: {logs_path}"], "sample": []}

    for requirement in log_requirements:
        want_level = requirement.get("level")
        want_event = requirement.get("event")
        need_fields = set(requirement.get("must_have_fields") or [])
        matched = False
        for entry in entries:
            if want_level and entry.get("level") != want_level:
                continue
            if want_event and entry.get("event") != want_event:
                continue
            if not need_fields.issubset(entry.keys()):
                continue
            matched = True
            samples.append(entry)
            break
        if not matched:
            missing.append(f"no log event {want_event} with fields {sorted(need_fields)}")
    return {"pass": not missing, "miss": missing, "sample": samples[:3]}


def maybe_llm_judge(payload: Dict[str, Any]) -> Dict[str, Any]:
    import os
    import yaml

    cfg = None
    cfg_path = pathlib.Path('.adrflow.yaml')
    if cfg_path.exists():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
        except yaml.YAMLError:
            cfg = None

    if not os.getenv('LLM_JUDGE') and not ((cfg or {}).get('llm_judge', {}).get('provider')):
        return payload
    from llm_judge import judge

    return judge('logs-vs-adr', payload, cfg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adr", default="docs/adr")
    parser.add_argument("--logs", default="reports/debug.log.jsonl")
    parser.add_argument("--out", default="reports/adr_log_check.json")
    args = parser.parse_args()

    specs = load_adr_specs(args.adr)
    total = {"items": [], "pass": True, "miss": []}
    for adr_id, spec in specs.items():
        result = check_logs_against_adr(spec, args.logs)
        total["items"].append({"adr_id": adr_id, **result})
        if not result["pass"]:
            total["pass"] = False
            total["miss"].extend([f"{adr_id}: {msg}" for msg in result["miss"]])

    total = maybe_llm_judge(total)
    write_json(args.out, total)
    if total["pass"]:
        ok("Log vs ADR PASS")
    else:
        fail("Log vs ADR FAIL:\n- " + "\n- ".join(total["miss"]))


if __name__ == "__main__":
    main()
