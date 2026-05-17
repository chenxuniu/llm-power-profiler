#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def main() -> None:
    args = parse_args()
    Path(args.reports_dir).mkdir(parents=True, exist_ok=True)
    for concurrency in parse_int_list(args.concurrency):
        prefix = f"{args.prefix}-c{concurrency}"
        run_checked(
            [
                sys.executable,
                "scripts/run_vllm_validation.py",
                "--target",
                args.target,
                "--model",
                args.model,
                "--gpus",
                args.gpus,
                "--proxy-port",
                str(args.proxy_port),
                "--interval",
                str(args.interval),
                "--requests",
                str(args.requests),
                "--concurrency",
                str(concurrency),
                "--max-tokens",
                str(args.max_tokens),
                "--reports-dir",
                args.reports_dir,
                "--prefix",
                prefix,
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small concurrency sweep against an existing LLM server.")
    parser.add_argument("--target", default="http://127.0.0.1:8001", help="Target OpenAI-compatible server.")
    parser.add_argument("--model", required=True, help="Model name to send in requests.")
    parser.add_argument("--gpus", default="0", help="GPU indices to sample.")
    parser.add_argument("--proxy-port", type=int, default=9000, help="Profiler proxy port.")
    parser.add_argument("--interval", type=float, default=0.1, help="Power sampling interval.")
    parser.add_argument("--requests", type=int, default=64, help="Requests per concurrency point.")
    parser.add_argument("--concurrency", default="1,4,8", help="Comma-separated concurrency points.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Requested max output tokens.")
    parser.add_argument("--reports-dir", default="reports", help="Report directory.")
    parser.add_argument("--prefix", default="sweep", help="Report filename prefix.")
    return parser.parse_args()


def parse_int_list(value: str) -> List[int]:
    result = []
    for part in value.split(","):
        part = part.strip()
        if part:
            result.append(int(part))
    if not result:
        raise ValueError("At least one concurrency value is required")
    return result


def run_checked(command: List[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
