from __future__ import annotations

import time
from typing import List, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from llm_power_profiler.nvml import NVMLMonitor, NVMLUnavailable
from llm_power_profiler.stats import SessionSnapshot


def run_watch(
    interval_s: float,
    duration_s: Optional[float],
    gpu_indices: Optional[List[int]] = None,
) -> None:
    console = Console()
    try:
        monitor = NVMLMonitor(gpu_indices=gpu_indices)
    except NVMLUnavailable as exc:
        console.print(_nvml_error_panel(exc))
        raise SystemExit(1) from exc
    start = time.monotonic()

    with Live(refresh_per_second=max(1, int(1 / interval_s))) as live:
        while True:
            live.update(render_gpu_samples(monitor.sample()))
            if duration_s is not None and time.monotonic() - start >= duration_s:
                break
            time.sleep(interval_s)


def render_gpu_samples(samples: list) -> Table:
    table = Table(title="llm-power-profiler watch")
    table.add_column("GPU")
    table.add_column("Name")
    table.add_column("Power")
    table.add_column("Util")
    table.add_column("Memory")
    table.add_column("Temp")

    for sample in samples:
        table.add_row(
            str(sample.index),
            sample.name,
            _fmt(sample.power_w, "W"),
            _fmt(sample.utilization_gpu_pct, "%"),
            _fmt_memory(sample.memory_used_gb, sample.memory_total_gb),
            _fmt(sample.temperature_c, "C"),
        )

    return table


def render_session(snapshot: SessionSnapshot, target: str, listening: str) -> Group:
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row("Target", target)
    header.add_row("Listening", listening)

    metrics = Table(title="LLM Power Profiler")
    metrics.add_column("Metric")
    metrics.add_column("Value", justify="right")
    metrics.add_row("Duration", f"{snapshot.duration_s:,.1f} s")
    metrics.add_row("Requests", f"{snapshot.request_count:,}")
    metrics.add_row("Prompt tokens", f"{snapshot.prompt_tokens:,}")
    metrics.add_row("Completion tokens", f"{snapshot.completion_tokens:,}")
    metrics.add_row("Total tokens", f"{snapshot.total_tokens:,}")
    metrics.add_row("Throughput", _fmt(snapshot.tokens_per_second, "tok/s"))
    if snapshot.power_error:
        metrics.add_row("Power telemetry", f"[yellow]disabled[/yellow]: {snapshot.power_error}")
    metrics.add_row("Avg power", _fmt(snapshot.avg_power_w, "W"))
    metrics.add_row("Peak power", _fmt(snapshot.peak_power_w, "W"))
    metrics.add_row("Energy", f"{snapshot.energy_kwh:.6f} kWh")
    metrics.add_row("J/token", _fmt(snapshot.joules_per_token, "J"))
    metrics.add_row("kWh/1M tokens", _fmt(snapshot.kwh_per_1m_tokens, "kWh"))
    metrics.add_row("Avg GPU util", _fmt(snapshot.avg_gpu_util_pct, "%"))
    metrics.add_row("Max memory", _fmt(snapshot.max_memory_gb, "GB"))

    return Group(
        Panel(header, title="Proxy"),
        metrics,
    )


def _fmt(value: Optional[float], unit: str) -> str:
    if value is None:
        return "-"
    return f"{value:,.2f} {unit}"


def _fmt_memory(used_gb: Optional[float], total_gb: Optional[float]) -> str:
    if used_gb is None or total_gb is None:
        return "-"
    return f"{used_gb:,.1f}/{total_gb:,.1f} GB"


def _nvml_error_panel(exc: NVMLUnavailable) -> Panel:
    return Panel(str(exc), title="NVML unavailable")
