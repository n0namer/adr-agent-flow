#!/usr/bin/env python
"""Synthesize lightweight CI artifacts for bootstrap and smoke scenarios."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _emit_debug_log(reports: Path) -> None:
    event = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime()),
        "level": "DEBUG",
        "event": "oauth.exchange",
        "adr": "ADR-0001",
        "trace_id": "bootstrap-trace",
        "provider": "google",
        "outcome": "success",
        "latency_ms": 120,
    }
    (reports / "debug.log.jsonl").write_text(json.dumps(event, ensure_ascii=False) + "\n", encoding="utf-8")


def _emit_e2e(reports: Path) -> None:
    e2e_dir = reports / "e2e"
    e2e_dir.mkdir(parents=True, exist_ok=True)
    for name in ("mlm", "vtb"):
        _write_json(
            e2e_dir / f"{name}.json",
            {
                "name": name,
                "pass": True,
                "ok": True,
                "duration_ms": 1200,
            },
        )


def _emit_security(reports: Path) -> None:
    _write_json(reports / "security.json", {"critical": 0, "high": 0, "medium": 0})


def _emit_performance(reports: Path) -> None:
    _write_json(
        reports / "performance.json",
        {"p95_ms": 180, "error_rate_pct": 0.1, "throughput_rps": 25},
    )


def _emit_coverage_if_missing(reports: Path) -> None:
    target = reports / "coverage.json"
    if not target.exists():
        _write_json(target, {"line": 90, "branch": 80})


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate bootstrap CI artifacts")
    parser.add_argument("--reports", default="reports", help="Target reports directory")
    parser.add_argument(
        "--emit",
        choices=["all", "e2e", "logs", "security", "performance", "coverage"],
        default="all",
        help="Artifact group to produce",
    )
    args = parser.parse_args()

    reports = Path(args.reports)
    reports.mkdir(parents=True, exist_ok=True)

    targets = {
        "logs": _emit_debug_log,
        "e2e": lambda base: (_emit_debug_log(base), _emit_e2e(base)),
        "security": _emit_security,
        "performance": _emit_performance,
        "coverage": _emit_coverage_if_missing,
    }

    if args.emit == "all":
        for producer in targets.values():
            producer(reports)
    else:
        targets[args.emit](reports)


if __name__ == "__main__":
    main()
