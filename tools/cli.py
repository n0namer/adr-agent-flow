"""Command line entrypoint for adrflow."""
from __future__ import annotations
import json
import pathlib
from typing import Any, Dict, Optional

import typer
import yaml

from ext_registry import discover_plugins
from llm_judge import register_builtin as register_builtin_judges
from gates import get_gate  # type: ignore

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _load_cfg() -> dict:
    path = pathlib.Path(".adrflow.yaml")
    if not path.exists():
        typer.echo("No .adrflow.yaml found. Run `adrflow init` first.", err=True)
        raise typer.Exit(2)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    register_builtin_judges()
    discover_plugins(cfg)
    return cfg


def _write_cfg(cfg: dict) -> None:
    path = pathlib.Path(".adrflow.yaml")
    path.write_text(
        yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _execute_gates(cfg: dict) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    all_ok = True

    for key in cfg.get("gates", {}).get("include", []):
        gate = get_gate(key)
        gate_result = gate.run(cfg)
        ok = bool(gate_result.ok)
        all_ok = all_ok and ok
        result[key] = {
            "ok": ok,
            "miss": list(gate_result.miss),
        }
        if getattr(gate_result, "artifact", None):
            result[key]["artifact"] = gate_result.artifact

    result["summary"] = {"ok": all_ok}
    return result


def _write_verify_report(cfg: dict, payload: Dict[str, Any]) -> pathlib.Path:
    reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "verify.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


@app.command()
def verify(
    json_out: bool = typer.Option(
        True, "--json/--no-json", help="Печатать JSON-результат выполнения гейтов"
    ),
    exit_code: bool = typer.Option(
        True,
        "--exit-code/--no-exit-code",
        help="Возвращать код выхода 0/1 в зависимости от summary.ok",
    ),
) -> None:
    """Locally execute configured gates and report JSON summary."""
    cfg = _load_cfg()
    payload = _execute_gates(cfg)
    _write_verify_report(cfg, payload)

    if json_out:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))

    if exit_code and not payload.get("summary", {}).get("ok", False):
        raise typer.Exit(1)


@app.command()
def init() -> None:  # pragma: no cover - scaffold stub
    """Bootstrap repository (placeholder)."""
    typer.echo("Bootstrap done (stub). Create PR with proposed files.")


@app.command()
def docs() -> None:
    """Print summary of current DoD artifacts and mandatory files."""
    cfg = _load_cfg()
    reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports/"))
    governance = pathlib.Path("governance/ci_checks.yaml")
    checks = yaml.safe_load(governance.read_text(encoding="utf-8")) if governance.exists() else {}
    required = checks.get("required_artifacts", [])
    payload = {
        "reports": str(reports_dir.resolve()),
        "required_artifacts": required,
        "present": [
            str(path.relative_to(pathlib.Path.cwd()))
            for path in reports_dir.glob("**/*")
            if path.is_file()
        ],
    }
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command()
def suggest() -> None:
    """Print minimal fixes based on the latest verify report."""
    cfg = _load_cfg()
    reports_dir = pathlib.Path(cfg.get("paths", {}).get("reports", "reports"))
    verify_path = reports_dir / "verify.json"
    if verify_path.exists():
        payload = json.loads(verify_path.read_text(encoding="utf-8"))
    else:
        payload = _execute_gates(cfg)
        _write_verify_report(cfg, payload)

    fixes: Dict[str, Any] = {"summary": payload.get("summary", {})}
    for gate, info in payload.items():
        if gate == "summary":
            continue
        if isinstance(info, dict) and not info.get("ok", True):
            fixes[gate] = info.get("miss", [])
    typer.echo(json.dumps(fixes, ensure_ascii=False, indent=2))


@app.command()
def adopt(
    mode: str = typer.Option("report-only", help="Target enforcement mode"),
    service: Optional[str] = typer.Option(None, help="Scope adoption to a specific service"),
    dry_run: bool = typer.Option(False, help="Preview changes without updating the config"),
) -> None:
    """Update enforcement mode (globally or per service)."""

    cfg = _load_cfg()
    cfg.setdefault("gates", {})["mode"] = mode
    if service:
        matrix = cfg.setdefault("enforcement_matrix", {})
        matrix[service] = mode

    if not dry_run:
        _write_cfg(cfg)

    typer.echo(
        json.dumps(
            {
                "mode": mode,
                "service": service,
                "dry_run": dry_run,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    app()
