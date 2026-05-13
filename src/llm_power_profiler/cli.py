from __future__ import annotations

from typing import Optional

import typer

from llm_power_profiler.doctor import run_doctor
from llm_power_profiler.proxy import run_proxy
from llm_power_profiler.tui import run_watch

app = typer.Typer(
    help="Measure watts, tokens, and joules per token for local LLM servers.",
    no_args_is_help=True,
)


@app.command()
def doctor() -> None:
    """Check NVIDIA/NVML telemetry availability."""
    run_doctor()


@app.command()
def watch(
    interval: float = typer.Option(1.0, help="Sampling interval in seconds."),
    duration: Optional[float] = typer.Option(None, help="Optional watch duration in seconds."),
) -> None:
    """Watch local NVIDIA GPU power, utilization, memory, and temperature."""
    run_watch(interval_s=interval, duration_s=duration)


@app.command()
def proxy(
    target: str = typer.Option(..., help="OpenAI-compatible server URL, e.g. http://localhost:8000."),
    host: str = typer.Option("127.0.0.1", help="Proxy bind host."),
    port: int = typer.Option(9000, help="Proxy bind port."),
    interval: float = typer.Option(0.5, help="GPU power sampling interval in seconds."),
) -> None:
    """Run a local proxy that connects token usage with GPU power telemetry."""
    run_proxy(target=target, host=host, port=port, interval_s=interval)

