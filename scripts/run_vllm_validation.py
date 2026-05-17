#!/usr/bin/env python3
from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List


def main() -> None:
    args = parse_args()
    reports = Path(args.reports_dir)
    reports.mkdir(parents=True, exist_ok=True)

    proxy_url = f"http://127.0.0.1:{args.proxy_port}"
    profiler_report = reports / f"{args.prefix}-profiler.json"
    traffic_jsonl = reports / f"{args.prefix}-traffic.jsonl"
    traffic_summary = reports / f"{args.prefix}-traffic-summary.json"

    wait_for_http(f"{args.target.rstrip('/')}/v1/models", "target server")
    proxy = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "llm_power_profiler.cli",
            "proxy",
            "--target",
            args.target,
            "--port",
            str(args.proxy_port),
            "--gpus",
            args.gpus,
            "--interval",
            str(args.interval),
            "--export",
            str(profiler_report),
        ]
    )
    try:
        wait_for_http(f"{proxy_url}/v1/models", "profiler proxy")
        run_checked(
            [
                sys.executable,
                "examples/traffic_generator.py",
                "--base-url",
                proxy_url,
                "--model",
                args.model,
                "--requests",
                str(args.requests),
                "--concurrency",
                str(args.concurrency),
                "--max-tokens",
                str(args.max_tokens),
                "--output",
                str(traffic_jsonl),
                "--summary",
                str(traffic_summary),
            ]
        )
    finally:
        stop_process(proxy, signal.SIGINT)

    print("Validation complete")
    print(f"Profiler report: {profiler_report}")
    print(f"Traffic summary: {traffic_summary}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run validation against an existing vLLM/OpenAI-compatible server.")
    parser.add_argument("--target", default="http://127.0.0.1:8001", help="Target OpenAI-compatible server.")
    parser.add_argument("--model", required=True, help="Model name to send in requests.")
    parser.add_argument("--gpus", default="0", help="GPU indices to sample.")
    parser.add_argument("--proxy-port", type=int, default=9000, help="Profiler proxy port.")
    parser.add_argument("--interval", type=float, default=0.1, help="Power sampling interval.")
    parser.add_argument("--requests", type=int, default=64, help="Total traffic requests.")
    parser.add_argument("--concurrency", type=int, default=4, help="Traffic concurrency.")
    parser.add_argument("--max-tokens", type=int, default=256, help="Requested max output tokens.")
    parser.add_argument("--reports-dir", default="reports", help="Report directory.")
    parser.add_argument("--prefix", default="vllm", help="Report filename prefix.")
    return parser.parse_args()


def wait_for_http(url: str, label: str, timeout_s: float = 60.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                if response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {label} at {url}")


def run_checked(command: List[str]) -> None:
    print("+ " + " ".join(command))
    subprocess.run(command, check=True)


def stop_process(process: subprocess.Popen, sig: signal.Signals) -> None:
    if process.poll() is not None:
        return
    process.send_signal(sig)
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


if __name__ == "__main__":
    main()
