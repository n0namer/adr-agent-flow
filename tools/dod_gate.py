#!/usr/bin/env python
"""Definition of Done aggregation logic."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

from common import fail, ok, read_json, write_json


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _flatten_required_artifacts(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, dict):
        items: List[str] = []
        for value in raw.values():
            items.extend(_flatten_required_artifacts(value))
        return items
    return [str(raw)]


def _collect_artifacts(entries: Iterable[str]) -> Dict[str, Any]:
    missing: List[str] = []
    present: List[str] = []
    for entry in entries:
        candidate = Path(entry)
        if candidate.exists():
            present.append(str(candidate))
        else:
            missing.append(str(candidate))
    return {"ok": not missing, "present": present, "missing": missing}


def _thresholds(section: Dict[str, Any]) -> Dict[str, Any]:
    if not section:
        return {}
    if isinstance(section, dict) and "thresholds" in section:
        nested = section.get("thresholds") or {}
        if isinstance(nested, dict):
            return nested
    return section


def evaluate_dod(dod_path: str, checks_path: str, reports_dir: str = "reports") -> Dict[str, Any]:
    """Calculate a structured DoD verdict."""

    reports_root = Path(reports_dir)
    dod = _load_yaml(Path(dod_path))
    checks = _load_yaml(Path(checks_path))

    summary_miss: List[str] = []

    adr_trace_report = read_json(reports_root / "adr_trace.json", {})
    adr_trace_ok = bool(adr_trace_report.get("pass"))
    adr_trace_miss = adr_trace_report.get("miss", []) if adr_trace_report else ["adr_trace.json missing"]
    if not adr_trace_ok:
        summary_miss.extend([f"adr-trace: {m}" for m in adr_trace_miss])

    log_report = read_json(reports_root / "adr_log_check.json", {})
    log_ok = bool(log_report.get("pass"))
    log_miss = log_report.get("miss", []) if log_report else ["adr_log_check.json missing"]
    if not log_ok:
        summary_miss.extend([f"log-vs-adr: {m}" for m in log_miss])

    coverage_data = read_json(reports_root / "coverage.json", {}) or {}
    coverage_actual = {
        "line": coverage_data.get("line"),
        "branch": coverage_data.get("branch"),
    }
    totals = coverage_data.get("totals", {}) if isinstance(coverage_data, dict) else {}
    if coverage_actual["line"] is None:
        coverage_actual["line"] = totals.get("percent_covered")
    if coverage_actual["branch"] is None:
        coverage_actual["branch"] = totals.get("percent_covered_branch")
    if coverage_actual["branch"] is None and coverage_data.get("meta", {}).get("branch_coverage") is False:
        coverage_actual["branch"] = coverage_actual["line"]
    coverage_thresholds = _thresholds(checks.get("coverage", {}))
    coverage_miss: List[str] = []
    coverage_ok = True
    if coverage_thresholds:
        line_req = coverage_thresholds.get("line")
        branch_req = coverage_thresholds.get("branch")
        if line_req is not None:
            current = coverage_actual.get("line")
            if current is None or current < line_req:
                coverage_ok = False
                coverage_miss.append(f"line coverage {current if current is not None else 'n/a'} < {line_req}")
        if branch_req is not None:
            current = coverage_actual.get("branch")
            if current is None or current < branch_req:
                coverage_ok = False
                coverage_miss.append(f"branch coverage {current if current is not None else 'n/a'} < {branch_req}")
    else:
        coverage_ok = bool(coverage_data)
        if not coverage_ok:
            coverage_miss.append("coverage.json missing")
    if not coverage_ok:
        summary_miss.extend([f"coverage: {m}" for m in coverage_miss])

    security_data = read_json(reports_root / "security.json", {}) or {}
    security_thresholds = _thresholds(checks.get("security", {}))
    security_ok = True
    security_miss: List[str] = []
    if security_thresholds:
        max_critical = security_thresholds.get("max_critical")
        max_high = security_thresholds.get("max_high")
        if max_critical is not None and security_data.get("critical", 0) > max_critical:
            security_ok = False
            security_miss.append(f"critical findings {security_data.get('critical', 0)} > {max_critical}")
        if max_high is not None and security_data.get("high", 0) > max_high:
            security_ok = False
            security_miss.append(f"high findings {security_data.get('high', 0)} > {max_high}")
    else:
        security_ok = bool(security_data)
        if not security_ok:
            security_miss.append("security.json missing")
    if not security_ok:
        summary_miss.extend([f"security: {m}" for m in security_miss])

    performance_thresholds = _thresholds(checks.get("performance", {}))
    performance_data = read_json(reports_root / "performance.json", {}) or {}
    performance_miss: List[str] = []
    performance_ok = True
    if performance_thresholds:
        for key, required in performance_thresholds.items():
            actual = performance_data.get(key)
            if actual is None:
                performance_ok = False
                performance_miss.append(f"performance metric {key} missing")
                continue
            if key.endswith("_ms") or key.endswith("_pct"):
                if actual > required:
                    performance_ok = False
                    performance_miss.append(f"{key} {actual} > {required}")
            else:
                if actual < required:
                    performance_ok = False
                    performance_miss.append(f"{key} {actual} < {required}")
    elif performance_data:
        performance_ok = True
    if not performance_ok:
        summary_miss.extend([f"performance: {m}" for m in performance_miss])

    mutation_threshold = checks.get("mutation", {}).get("score")
    mutation_data = read_json(reports_root / "mutation.json", {}) or {}
    mutation_ok = True
    mutation_miss: List[str] = []
    if mutation_threshold is not None and mutation_threshold > 0:
        actual_score = mutation_data.get("score")
        if actual_score is None or actual_score < mutation_threshold:
            mutation_ok = False
            mutation_miss.append(
                f"mutation score {actual_score if actual_score is not None else 'n/a'} < {mutation_threshold}"
            )
    if not mutation_ok:
        summary_miss.extend([f"mutation: {m}" for m in mutation_miss])

    required_artifacts = _flatten_required_artifacts(checks.get("required_artifacts"))
    artifacts_state = _collect_artifacts(required_artifacts)
    if not artifacts_state["ok"]:
        summary_miss.extend([f"artifact missing: {item}" for item in artifacts_state["missing"]])

    e2e_entries = dod.get("evidence", {}).get("e2e", [])
    e2e_reports: Dict[str, Any] = {}
    e2e_ok = True
    for entry in e2e_entries:
        entry_path = Path(entry)
        data = read_json(entry_path, {})
        step_ok = bool(data.get("ok")) or bool(data.get("pass"))
        if not entry_path.exists():
            step_ok = False
            data = {}
        e2e_reports[str(entry_path)] = {"ok": step_ok, "data": data}
        if not step_ok:
            e2e_ok = False
            summary_miss.append(f"e2e: {entry_path} not ok")

    result = {
        "adr_trace": {
            "ok": adr_trace_ok,
            "report": str((reports_root / "adr_trace.json").resolve()),
            "miss": adr_trace_miss,
        },
        "logs": {
            "ok": log_ok,
            "report": str((reports_root / "adr_log_check.json").resolve()),
            "miss": log_miss,
        },
        "coverage": {
            "ok": coverage_ok,
            "actual": {"line": coverage_actual.get("line"), "branch": coverage_actual.get("branch"), "raw": coverage_data},
            "thresholds": coverage_thresholds,
            "miss": coverage_miss,
        },
        "security": {
            "ok": security_ok,
            "actual": security_data,
            "thresholds": security_thresholds,
            "miss": security_miss,
        },
        "performance": {
            "ok": performance_ok,
            "actual": performance_data,
            "thresholds": performance_thresholds,
            "miss": performance_miss,
        },
        "mutation": {
            "ok": mutation_ok,
            "actual": mutation_data,
            "threshold": mutation_threshold,
            "miss": mutation_miss,
        },
        "required_artifacts": artifacts_state,
        "e2e": {"ok": e2e_ok, "reports": e2e_reports},
    }

    result["summary"] = {"ok": not summary_miss, "miss": summary_miss}
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dod", required=True)
    parser.add_argument("--checks", required=True)
    parser.add_argument("--out", default="reports/dod_gate.json")
    parser.add_argument("--reports", default="reports")
    args = parser.parse_args()

    payload = evaluate_dod(args.dod, args.checks, reports_dir=args.reports)
    write_json(args.out, payload)

    if payload["summary"]["ok"]:
        ok("DoD Gate PASS")
    else:
        fail("DoD Gate FAIL:\n- " + "\n- ".join(payload["summary"]["miss"]))


if __name__ == "__main__":
    main()
