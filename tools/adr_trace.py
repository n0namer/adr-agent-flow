#!/usr/bin/env python
import argparse
import pathlib
import re
from typing import Dict, List

from common import fail, load_yaml_front_matter, ok, write_json

CODE_TAG = re.compile(r"ADR:\s*(ADR-\d+)", re.IGNORECASE)
TEST_TAG = re.compile(r"TEST-ADR:\s*(ADR-\d+)", re.IGNORECASE)


def scan_adr(adr_dir: str) -> List[str]:
    ids = []
    for path in pathlib.Path(adr_dir).glob("ADR-*.md"):
        front_matter = load_yaml_front_matter(str(path))
        if front_matter.get("adr_id"):
            ids.append(front_matter["adr_id"])
    return sorted(set(ids))


def scan_repo(src_dir: str) -> Dict[str, Dict[str, List[str]]]:
    result: Dict[str, Dict[str, List[str]]] = {}
    src_path = pathlib.Path(src_dir)
    for path in src_path.rglob("*.*"):
        lowered = str(path).lower()
        if any(skip in lowered for skip in ["/.git/", "/reports/", "/docs/adr/", "/node_modules/", "/.venv/"]):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for match in CODE_TAG.finditer(text):
            adr = match.group(1).upper()
            result.setdefault(adr, {}).setdefault("code", []).append(str(path))
        for match in TEST_TAG.finditer(text):
            adr = match.group(1).upper()
            result.setdefault(adr, {}).setdefault("tests", []).append(str(path))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default=".")
    parser.add_argument("--adr", default="docs/adr")
    parser.add_argument("--out", default="reports/adr_trace.json")
    args = parser.parse_args()

    declared = set(scan_adr(args.adr))
    traced = scan_repo(args.src)

    report = {"items": [], "pass": True, "miss": []}
    for adr in sorted(declared):
        code_refs = traced.get(adr, {}).get("code", [])
        test_refs = traced.get(adr, {}).get("tests", [])
        item = {"adr_id": adr, "code": code_refs, "tests": test_refs, "ok": bool(code_refs and test_refs)}
        report["items"].append(item)
        if not item["ok"]:
            report["pass"] = False
            if not code_refs:
                report["miss"].append(f"{adr}: no code references (tag 'ADR: {adr}')")
            if not test_refs:
                report["miss"].append(f"{adr}: no test references (tag 'TEST-ADR: {adr}')")

    write_json(args.out, report)
    if report["pass"]:
        ok("ADR trace PASS")
    else:
        fail("ADR trace FAIL:\n- " + "\n- ".join(report["miss"]))


if __name__ == "__main__":
    main()
