"""Tests for intentionally failing report bundle generation."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

try:  # pragma: no cover - dependency guard
    import yaml  # type: ignore  # noqa: F401  (ensure availability for dod_gate)
except ModuleNotFoundError:  # pragma: no cover - dependency guard
    pytest.skip("PyYAML is required for DoD evaluation tests", allow_module_level=True)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.bootstrap_reports import emit_failure_bundle
from tools.dod_gate import evaluate_dod


def _write_yaml(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_failure_bundle_triggers_dod_misses(tmp_path) -> None:
    reports = tmp_path / "reports"
    emit_failure_bundle(reports)

    dod_path = tmp_path / "DoD.yaml"
    e2e_reports = [
        str(reports / "e2e" / "mlm.json"),
        str(reports / "e2e" / "vtb.json"),
    ]
    _write_yaml(
        dod_path,
        {
            "evidence": {
                "e2e": e2e_reports,
            }
        },
    )

    checks_path = tmp_path / "ci_checks.yaml"
    debug_log = reports / "debug.log.jsonl"
    _write_yaml(
        checks_path,
        {
            "coverage": {"thresholds": {"line": 85, "branch": 75}},
            "security": {"thresholds": {"max_critical": 0, "max_high": 0}},
            "performance": {
                "thresholds": {"p95_ms": 300, "error_rate_pct": 0.5, "throughput_rps": 20}
            },
            "mutation": {"score": 0.8},
            "required_artifacts": [
                str(reports / "adr_trace.json"),
                str(reports / "adr_log_check.json"),
                str(debug_log),
            ],
        },
    )

    payload = evaluate_dod(str(dod_path), str(checks_path), reports_dir=str(reports))

    summary = payload["summary"]
    assert summary["miss"], "Summary must list detected problems"
    assert not summary["ok"], "DoD summary should fail for the faulty bundle"
    assert any("adr-trace" in miss for miss in summary["miss"])
    assert any("coverage:" in miss for miss in summary["miss"])
    assert any("security:" in miss for miss in summary["miss"])
    assert any("performance:" in miss for miss in summary["miss"])
    assert any("e2e:" in miss for miss in summary["miss"])

    coverage = payload["coverage"]
    assert not coverage["ok"]
    assert any("line coverage" in item for item in coverage["miss"])

    security = payload["security"]
    assert not security["ok"]
    assert any("critical findings" in item for item in security["miss"])

    performance = payload["performance"]
    assert not performance["ok"]
    assert any("p95_ms" in item or "throughput" in item for item in performance["miss"])

    mutation = payload["mutation"]
    assert not mutation["ok"]
    assert any("mutation score" in item for item in mutation["miss"])

    artifacts = payload["required_artifacts"]
    assert not artifacts["ok"]
    assert str(debug_log) in artifacts["missing"]

    e2e = payload["e2e"]
    assert not e2e["ok"]
    assert not (reports / "e2e" / "vtb.json").exists()
