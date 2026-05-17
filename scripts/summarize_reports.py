#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


FIELDS = [
    "run",
    "requests",
    "completed",
    "errors",
    "total_tokens",
    "traffic_tokens_per_second",
    "latency_avg_s",
    "latency_p50_s",
    "latency_p95_s",
    "duration_s",
    "active_duration_s",
    "avg_power_w",
    "peak_power_w",
    "active_avg_power_w",
    "energy_kwh",
    "active_energy_kwh",
    "joules_per_token",
    "active_joules_per_token",
    "kwh_per_1m_tokens",
    "active_kwh_per_1m_tokens",
]


def main() -> None:
    args = parse_args()
    rows = collect_rows(Path(args.reports_dir))
    if args.csv:
        write_csv(Path(args.csv), rows)
    print_markdown(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize profiler and traffic reports.")
    parser.add_argument("--reports-dir", default="reports", help="Report directory.")
    parser.add_argument("--csv", default=None, help="Optional CSV output path.")
    return parser.parse_args()


def collect_rows(reports_dir: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for profiler_path in sorted(reports_dir.glob("*-profiler.json")):
        prefix = profiler_path.name[: -len("-profiler.json")]
        traffic_path = reports_dir / f"{prefix}-traffic-summary.json"
        profiler = read_json(profiler_path)
        traffic = read_json(traffic_path) if traffic_path.exists() else {}
        rows.append(build_row(prefix, profiler, traffic))
    return rows


def build_row(run: str, profiler: Dict[str, Any], traffic: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "run": run,
        "requests": profiler.get("request_count"),
        "completed": traffic.get("completed"),
        "errors": traffic.get("errors"),
        "total_tokens": profiler.get("total_tokens") or traffic.get("total_tokens"),
        "traffic_tokens_per_second": traffic.get("tokens_per_second"),
        "latency_avg_s": traffic.get("latency_avg_s"),
        "latency_p50_s": traffic.get("latency_p50_s"),
        "latency_p95_s": traffic.get("latency_p95_s"),
        "duration_s": profiler.get("duration_s"),
        "active_duration_s": profiler.get("active_duration_s"),
        "avg_power_w": profiler.get("avg_power_w"),
        "peak_power_w": profiler.get("peak_power_w"),
        "active_avg_power_w": profiler.get("active_avg_power_w"),
        "energy_kwh": profiler.get("energy_kwh"),
        "active_energy_kwh": profiler.get("active_energy_kwh"),
        "joules_per_token": profiler.get("joules_per_token"),
        "active_joules_per_token": profiler.get("active_joules_per_token"),
        "kwh_per_1m_tokens": profiler.get("kwh_per_1m_tokens"),
        "active_kwh_per_1m_tokens": profiler.get("active_kwh_per_1m_tokens"),
    }


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {path}")


def print_markdown(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("No *-profiler.json files found.")
        return
    compact_fields = [
        "run",
        "total_tokens",
        "latency_p50_s",
        "latency_p95_s",
        "active_avg_power_w",
        "active_joules_per_token",
        "active_kwh_per_1m_tokens",
    ]
    print("| " + " | ".join(compact_fields) + " |")
    print("| " + " | ".join(["---"] * len(compact_fields)) + " |")
    for row in rows:
        print("| " + " | ".join(format_value(row.get(field)) for field in compact_fields) + " |")


def format_value(value: Optional[Any]) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


if __name__ == "__main__":
    main()
