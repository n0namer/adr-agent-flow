"""Builtin gate wrapper for DoD aggregation."""
from ..registry import register_gate
from ..base import Gate, GateResult
import pathlib


@register_gate
class DoDGate(Gate):
    key = "dod-gate"
    title = "DoD Gate"

    def run(self, cfg):
        reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/"))
        dod_path = cfg.get("paths", {}).get("dod_file", "docs/dod/DoD.yaml")
        out_path = reports_dir / "dod_gate.json"
        rc = self.run_cmd(
            f"python tools/dod_gate.py --dod {dod_path} --checks governance/ci_checks.yaml --out {out_path}"
        )
        data = self.read_json(str(out_path))
        summary = data.get("summary", {}) if data else {}
        ok = (rc == 0) and bool(summary.get("ok"))
        miss = summary.get("miss", []) if summary else ["dod_gate.json missing or invalid"]
        return GateResult(ok=ok, miss=miss, artifact=str(out_path))
