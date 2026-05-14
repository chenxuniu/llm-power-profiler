from __future__ import annotations

import json
import threading
from typing import Dict, List, Optional

import httpx
import uvicorn
from rich.console import Console
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from llm_power_profiler.export import write_json_report
from llm_power_profiler.nvml import NVMLMonitor, NVMLUnavailable
from llm_power_profiler.stats import SessionStats
from llm_power_profiler.tui import render_session
from llm_power_profiler.usage import parse_openai_usage


HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
    "content-encoding",
}


def run_proxy(
    target: str,
    host: str,
    port: int,
    interval_s: float,
    export_path: Optional[str] = None,
    gpu_indices: Optional[List[int]] = None,
) -> None:
    stats = SessionStats()
    stop_event = threading.Event()
    console = Console()

    sampler_thread = threading.Thread(
        target=_sample_power_loop,
        args=(stats, interval_s, stop_event, gpu_indices),
        daemon=True,
    )
    sampler_thread.start()

    dashboard_thread = threading.Thread(
        target=_dashboard_loop,
        args=(stats, target, host, port, stop_event, console),
        daemon=True,
    )
    dashboard_thread.start()

    app = create_app(target=target, stats=stats)
    try:
        uvicorn.run(app, host=host, port=port, log_level="warning")
    finally:
        stop_event.set()
        sampler_thread.join(timeout=2)
        dashboard_thread.join(timeout=2)
        if export_path:
            write_json_report(export_path, stats.snapshot().to_dict())


def create_app(target: str, stats: SessionStats) -> Starlette:
    async def forward(request: Request) -> Response:
        target_url = f"{target.rstrip('/')}{request.url.path}"
        if request.url.query:
            target_url = f"{target_url}?{request.url.query}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }
        body = await request.body()

        async with httpx.AsyncClient(timeout=None) as client:
            upstream = await client.request(
                request.method,
                target_url,
                headers=headers,
                content=body,
            )

        usage = _extract_usage(upstream)
        if usage is not None:
            stats.record_request(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )

        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return Starlette(routes=[Route("/{path:path}", forward, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])])


def _extract_usage(response: httpx.Response) -> Optional[Dict[str, int]]:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return None

    try:
        payload = response.json()
    except (json.JSONDecodeError, ValueError):
        return None

    return parse_openai_usage(payload)


def _sample_power_loop(
    stats: SessionStats,
    interval_s: float,
    stop_event: threading.Event,
    gpu_indices: Optional[List[int]],
) -> None:
    try:
        monitor = NVMLMonitor(gpu_indices=gpu_indices)
    except NVMLUnavailable as exc:
        stats.set_power_error(str(exc))
        return

    while not stop_event.is_set():
        samples = monitor.sample()
        total_power_w = sum(sample.power_w or 0.0 for sample in samples)
        avg_util = _average([sample.utilization_gpu_pct for sample in samples])
        max_memory_gb = max((sample.memory_used_gb or 0.0 for sample in samples), default=0.0)
        stats.record_power(
            total_power_w=total_power_w,
            avg_gpu_util_pct=avg_util,
            max_memory_gb=max_memory_gb,
        )
        stop_event.wait(interval_s)


def _dashboard_loop(
    stats: SessionStats,
    target: str,
    host: str,
    port: int,
    stop_event: threading.Event,
    console: Console,
) -> None:
    while not stop_event.is_set():
        console.clear()
        console.print(render_session(stats.snapshot(), target=target, listening=f"http://{host}:{port}"))
        stop_event.wait(1.0)


def _average(values: list[Optional[float]]) -> Optional[float]:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)
