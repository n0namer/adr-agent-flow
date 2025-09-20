"""Builtin gate wrapper for log analysis."""
from ..registry import register_gate
from ..base import Gate, GateResult
import pathlib


@register_gate
class LogVsAdrGate(Gate):
    key = "log-vs-adr"
    title = "Logs vs ADR"

    def run(self, cfg):
        reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/"))
        logs_path = reports_dir / "debug.log.jsonl"
        out_path = reports_dir / "adr_log_check.json"
        rc = self.run_cmd(f"python tools/log_analyzer.py --adr docs/adr --logs {logs_path} --out {out_path}")
        data = self.read_json(str(out_path))
        ok = (rc == 0) and bool(data.get("pass"))
        miss = data.get("miss", []) if data else ["adr_log_check.json missing or invalid"]
        return GateResult(ok=ok, miss=miss, artifact=str(out_path))
