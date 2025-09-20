#!/usr/bin/env python
import json
import subprocess
import sys
import pathlib


def run(cmd: str) -> int:
    print(f"[adrflow] $ {cmd}", flush=True)
    return subprocess.call(cmd, shell=True)


def main() -> None:
    reports = pathlib.Path("reports")
    reports.mkdir(exist_ok=True, parents=True)

    rc = run("python tools/cli.py verify --json --exit-code")

    verify: dict[str, object] = {}
    verify_path = reports / "verify.json"
    if verify_path.exists():
        verify = json.loads(verify_path.read_text(encoding="utf-8"))

    if not verify:
        print(
            json.dumps(
                {
                    "summary": {"ok": rc == 0},
                    "_hint": "cli.py не записал verify.json — проверь версию пакета",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(rc)

    print(json.dumps(verify, ensure_ascii=False, indent=2))
    sys.exit(0 if verify.get("summary", {}).get("ok") else 1)


if __name__ == "__main__":
    main()
