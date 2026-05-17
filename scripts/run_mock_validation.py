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

    mock_url = f"http://127.0.0.1:{args.mock_port}"
    proxy_url = f"http://127.0.0.1:{args.proxy_port}"
    profiler_report = reports / f"{args.prefix}-profiler.json"
    traffic_jsonl = reports / f"{args.prefix}-traffic.jsonl"
    traffic_summary = reports / f"{args.prefix}-traffic-summary.json"

    mock = subprocess.Popen(
        [
            sys.executable,
            "examples/mock_openai_server.py",
            "--port",
            str(args.mock_port),
        ]
    )
    proxy = None
    try:
        wait_for_http(f"{mock_url}/v1/models", "mock server")
        proxy = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "llm_power_profiler.cli",
                "proxy",
                "--target",
                mock_url,
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
        wait_for_http(f"{proxy_url}/v1/models", "profiler proxy")
        run_checked(
            [
                sys.executable,
                "examples/traffic_generator.py",
                "--base-url",
                proxy_url,
                "--model",
                "mock-llm",
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
        if proxy is not None:
            stop_process(proxy, signal.SIGINT)
        stop_process(mock, signal.SIGTERM)

    print("Validation complete")
    print(f"Profiler report: {profiler_report}")
    print(f"Traffic summary: {traffic_summary}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run mock end-to-end validation.")
    parser.add_argument("--gpus", default="0", help="GPU indices to sample.")
    parser.add_argument("--mock-port", type=int, default=8001, help="Mock server port.")
    parser.add_argument("--proxy-port", type=int, default=9000, help="Profiler proxy port.")
    parser.add_argument("--interval", type=float, default=0.1, help="Power sampling interval.")
    parser.add_argument("--requests", type=int, default=16, help="Total traffic requests.")
    parser.add_argument("--concurrency", type=int, default=4, help="Traffic concurrency.")
    parser.add_argument("--max-tokens", type=int, default=128, help="Requested max output tokens.")
    parser.add_argument("--reports-dir", default="reports", help="Report directory.")
    parser.add_argument("--prefix", default="mock", help="Report filename prefix.")
    return parser.parse_args()


def wait_for_http(url: str, label: str, timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:
                if response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
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
