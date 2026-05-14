#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    started_at = time.time()
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(send_chat_request, args, request_id)
            for request_id in range(args.requests)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                f"request={result['request_id']} status={result['status']} "
                f"latency_s={result['latency_s']:.3f} total_tokens={result.get('total_tokens', 0)}"
            )

    output_path.write_text(
        "".join(json.dumps(result, sort_keys=True) + "\n" for result in sorted(results, key=lambda x: x["request_id"])),
        encoding="utf-8",
    )

    summary = summarize(results, started_at=time.time() - started_at)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate reproducible OpenAI-compatible chat traffic.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9000", help="Profiler or server base URL.")
    parser.add_argument("--model", default="mock-llm", help="Model name sent in the request payload.")
    parser.add_argument("--requests", type=int, default=16, help="Total number of requests.")
    parser.add_argument("--concurrency", type=int, default=4, help="Concurrent worker count.")
    parser.add_argument("--max-tokens", type=int, default=128, help="Requested max output tokens.")
    parser.add_argument("--prompt", default="Explain joules per token in one paragraph.", help="Prompt text.")
    parser.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout in seconds.")
    parser.add_argument("--output", default="reports/traffic.jsonl", help="Per-request JSONL output.")
    parser.add_argument("--summary", default="reports/traffic-summary.json", help="Summary JSON output.")
    return parser.parse_args()


def send_chat_request(args: argparse.Namespace, request_id: int) -> Dict[str, Any]:
    url = f"{args.base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": f"{args.prompt}\nRequest id: {request_id}",
            }
        ],
        "max_tokens": args.max_tokens,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started_at = time.time()
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            response_body = response.read()
            status = response.status
        latency_s = time.time() - started_at
        data = json.loads(response_body.decode("utf-8"))
        usage = data.get("usage", {}) if isinstance(data, dict) else {}
        return {
            "request_id": request_id,
            "status": status,
            "latency_s": latency_s,
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "request_id": request_id,
            "status": "error",
            "latency_s": time.time() - started_at,
            "error": str(exc),
        }


def summarize(results: List[Dict[str, Any]], started_at: float) -> Dict[str, Any]:
    completed = [result for result in results if isinstance(result["status"], int) and result["status"] < 500]
    total_tokens = sum(int(result.get("total_tokens") or 0) for result in completed)
    latencies = sorted(float(result["latency_s"]) for result in completed)
    return {
        "requests": len(results),
        "completed": len(completed),
        "errors": len(results) - len(completed),
        "wall_time_s": started_at,
        "total_tokens": total_tokens,
        "tokens_per_second": total_tokens / started_at if started_at > 0 else None,
        "latency_avg_s": sum(latencies) / len(latencies) if latencies else None,
        "latency_p50_s": percentile(latencies, 50),
        "latency_p95_s": percentile(latencies, 95),
    }


def percentile(values: List[float], pct: float) -> Any:
    if not values:
        return None
    index = round((len(values) - 1) * (pct / 100.0))
    return values[index]


if __name__ == "__main__":
    main()
