"""Builtin gate wrapper for ADR trace."""
from ..registry import register_gate
from ..base import Gate, GateResult
import pathlib


@register_gate
class AdrTraceGate(Gate):
    key = "adr-trace"
    title = "ADR Trace"

    def run(self, cfg):
        reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/"))
        out_path = reports_dir / "adr_trace.json"
        rc = self.run_cmd(f"python tools/adr_trace.py --src . --adr docs/adr --out {out_path}")
        data = self.read_json(str(out_path))
        ok = (rc == 0) and bool(data.get("pass"))
        miss = data.get("miss", []) if data else ["adr_trace.json missing or invalid"]
        return GateResult(ok=ok, miss=miss, artifact=str(out_path))
