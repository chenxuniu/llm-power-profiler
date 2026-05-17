#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def main() -> None:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": sys.version,
        "commands": {
            "nvidia_smi": run_command(["nvidia-smi"]),
            "doctor": run_command(["llm-power-profiler", "doctor", "--gpus", args.gpus]),
        },
    }

    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect environment metadata for validation runs.")
    parser.add_argument("--gpus", default="0", help="GPU indices passed to llm-power-profiler doctor.")
    parser.add_argument("--output", default="reports/env.json", help="Output JSON path.")
    return parser.parse_args()


def run_command(command: List[str]) -> Dict[str, Any]:
    try:
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return {
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


if __name__ == "__main__":
    main()
