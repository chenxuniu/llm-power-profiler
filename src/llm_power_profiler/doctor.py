from __future__ import annotations

from rich.console import Console
from rich.table import Table

from typing import List, Optional

from llm_power_profiler.nvml import NVMLMonitor, NVMLUnavailable


def run_doctor(gpu_indices: Optional[List[int]] = None) -> None:
    console = Console()
    table = Table(title="llm-power-profiler doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")

    try:
        monitor = NVMLMonitor(gpu_indices=gpu_indices)
        gpus = monitor.sample()
    except NVMLUnavailable as exc:
        table.add_row("NVML", "[red]FAIL[/red]", str(exc))
        console.print(table)
        raise SystemExit(1) from exc

    table.add_row("NVML", "[green]OK[/green]", "NVIDIA Management Library is available")
    table.add_row("GPU count", "[green]OK[/green]", str(len(gpus)))

    for gpu in gpus:
        power_status = "[green]OK[/green]" if gpu.power_w is not None else "[yellow]MISSING[/yellow]"
        table.add_row(
            f"GPU {gpu.index} power telemetry",
            power_status,
            gpu.name,
        )

    console.print(table)
