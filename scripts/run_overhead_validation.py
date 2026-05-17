#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def main() -> None:
    args = parse_args()
    reports = Path(args.reports_dir)
    reports.mkdir(parents=True, exist_ok=True)

    run_checked(
        [
            sys.executable,
            "examples/traffic_generator.py",
            "--base-url",
            args.target,
            "--model",
            args.model,
            "--requests",
            str(args.requests),
            "--concurrency",
            str(args.concurrency),
            "--max-tokens",
            str(args.max_tokens),
            "--output",
            str(reports / f"{args.prefix}-direct-traffic.jsonl"),
            "--summary",
            str(reports / f"{args.prefix}-direct-summary.json"),
        ]
    )

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
            str(args.concurrency),
            "--max-tokens",
            str(args.max_tokens),
            "--reports-dir",
            str(reports),
            "--prefix",
            f"{args.prefix}-proxied",
        ]
    )

    print("Overhead validation complete")
    print(f"Direct summary: {reports / f'{args.prefix}-direct-summary.json'}")
    print(f"Proxied summary: {reports / f'{args.prefix}-proxied-traffic-summary.json'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run direct-vs-proxy overhead validation.")
    parser.add_argument("--target", default="http://127.0.0.1:8001", help="Target OpenAI-compatible server.")
    parser.add_argument("--model", required=True, help="Model name to send in requests.")
    parser.add_argument("--gpus", default="0", help="GPU indices to sample.")
    parser.add_argument("--proxy-port", type=int, default=9000, help="Profiler proxy port.")
    parser.add_argument("--interval", type=float, default=0.1, help="Power sampling interval.")
    parser.add_argument("--requests", type=int, default=64, help="Total traffic requests.")
    parser.add_argument("--concurrency", type=int, default=4, help="Traffic concurrency.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Requested max output tokens.")
    parser.add_argument("--reports-dir", default="reports", help="Report directory.")
    parser.add_argument("--prefix", default="overhead", help="Report filename prefix.")
    return parser.parse_args()


def run_checked(command: List[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
