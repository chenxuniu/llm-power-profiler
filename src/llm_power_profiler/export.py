from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Mapping, Optional

from llm_power_profiler.stats import SessionStats


def write_json_report(path: str, payload: Mapping[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_proxy_report(
    stats: SessionStats,
    target: str,
    host: str,
    port: int,
    interval_s: float,
    gpu_indices: Optional[List[int]],
) -> Mapping[str, Any]:
    report = stats.snapshot().to_dict()
    report["metadata"] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "host": host,
        "port": port,
        "interval_s": interval_s,
        "gpu_indices": gpu_indices,
    }
    return report
