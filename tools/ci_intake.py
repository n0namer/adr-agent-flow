#!/usr/bin/env python
"""CI intake orchestrator for Codex/LLM agents."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

import yaml

from common import read_json, write_json
from dod_gate import evaluate_dod


def run_cmd(cmd: List[str], *, check: bool = False) -> int:
    """Run a command and stream output."""

    print(f"[ci_intake] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.returncode


def load_cfg(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def ensure_reports_dir(cfg: Dict[str, Any]) -> Path:
    reports_path = Path(cfg.get("paths", {}).get("reports", "reports"))
    reports_path.mkdir(parents=True, exist_ok=True)
    return reports_path


def fetch_artifacts(args: argparse.Namespace, reports_dir: Path) -> None:
    if not args.fetch:
        return

    if args.gh_cli and shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI not found but --fetch requested")

    if args.run_id is None:
        raise RuntimeError("--run-id is required when --fetch is enabled")

    dest = args.download_dir or reports_dir
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    if args.gh_cli:
        cmd = [
            "gh",
            "run",
            "download",
            str(args.run_id),
            "-D",
            str(dest),
        ]
        if args.artifact:
            cmd.extend(["-n", args.artifact])
        run_cmd(cmd, check=True)
    else:
        import requests

        token = os.environ.get("GH_TOKEN")
        if not token:
            raise RuntimeError("GH_TOKEN must be set for REST artifact download")
        if not (args.owner and args.repo):
            raise RuntimeError("--owner and --repo are required for REST artifact download")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        api = f"https://api.github.com/repos/{args.owner}/{args.repo}/actions/runs/{args.run_id}/artifacts"
        response = requests.get(api, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("artifacts", [])
        target = None
        if args.artifact:
            for item in items:
                if item.get("name") == args.artifact:
                    target = item
                    break
        else:
            target = items[0] if items else None
        if not target:
            raise RuntimeError("Artifact not found in run download response")
        download_url = target.get("archive_download_url")
        response = requests.get(download_url, headers=headers, timeout=60)
        response.raise_for_status()
        archive_path = dest / "artifact.zip"
        archive_path.write_bytes(response.content)
        shutil.unpack_archive(str(archive_path), str(dest))
        archive_path.unlink()


def collect_verify_summary(reports_dir: Path, rerun: bool) -> Dict[str, Any]:
    if rerun:
        run_cmd([
            "python",
            "tools/cli.py",
            "verify",
            "--json",
            "--exit-code",
        ])
    verify_report = read_json(reports_dir / "verify.json", {}) or {}
    return verify_report


def aggregate(args: argparse.Namespace) -> Dict[str, Any]:
    cfg = load_cfg(Path(".adrflow.yaml"))
    reports_dir = ensure_reports_dir(cfg)

    fetch_artifacts(args, reports_dir)

    verify_report = collect_verify_summary(reports_dir, rerun=not args.skip_verify)
    verify_ok = verify_report.get("summary", {}).get("ok", True)

    dod_file = cfg.get("paths", {}).get("dod_file", "docs/dod/DoD.yaml")
    checks_file = args.checks or "governance/ci_checks.yaml"
    dod_payload = evaluate_dod(dod_file, checks_file, reports_dir=str(reports_dir))
    dod_payload.setdefault("summary", {})["mode"] = args.mode

    summary_miss: List[str] = list(dod_payload.get("summary", {}).get("miss", []))
    if not verify_ok:
        for gate, gate_report in verify_report.items():
            if gate == "summary":
                continue
            if isinstance(gate_report, dict) and not gate_report.get("ok", True):
                for miss in gate_report.get("miss", []):
                    summary_miss.append(f"{gate}: {miss}")

    summary_ok = bool(dod_payload.get("summary", {}).get("ok", False) and verify_ok)

    metadata = {
        "mode": args.mode,
        "owner": args.owner,
        "repo": args.repo,
        "branch": args.branch,
        "run_id": args.run_id,
        "pull_request": args.pull,
        "artifact": args.artifact,
        "fetched": bool(args.fetch),
    }

    final_payload: Dict[str, Any] = {
        "metadata": {k: v for k, v in metadata.items() if v is not None},
        "verify": verify_report,
        "dod": dod_payload,
    }
    summary = {
        "ok": summary_ok,
        "miss": summary_miss,
        "mode": args.mode,
        "source": "ci_intake",
    }
    final_payload["summary"] = summary

    return final_payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch CI artifacts and evaluate DoD gates")
    parser.add_argument("--mode", choices=["report-only", "guard", "enforce"], default="report-only")
    parser.add_argument("--fetch", action="store_true", help="Download artifacts via GitHub API/CLI")
    parser.add_argument("--gh-cli", action="store_true", help="Use GitHub CLI for downloads")
    parser.add_argument("--run-id", type=int, help="GitHub Actions run identifier")
    parser.add_argument("--artifact", help="Specific artifact name to download")
    parser.add_argument("--download-dir", help="Destination folder for downloaded artifacts")
    parser.add_argument("--owner", help="GitHub repository owner")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--branch", help="Git branch associated with the run")
    parser.add_argument("--pull", type=int, help="Pull request number")
    parser.add_argument("--checks", help="Path to ci_checks.yaml override")
    parser.add_argument("--skip-verify", action="store_true", help="Do not rerun adrflow verify locally")
    parser.add_argument("--out", default="reports/dod_gate.json", help="Where to write the aggregated JSON")
    args = parser.parse_args()

    payload = aggregate(args)
    write_json(args.out, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if payload["summary"]["ok"]:
        raise SystemExit(0)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
