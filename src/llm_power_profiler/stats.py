from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class SessionSnapshot:
    duration_s: float
    request_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    tokens_per_second: Optional[float]
    avg_power_w: Optional[float]
    peak_power_w: Optional[float]
    power_error: Optional[str]
    energy_j: float
    energy_wh: float
    energy_kwh: float
    joules_per_token: Optional[float]
    kwh_per_1m_tokens: Optional[float]
    avg_gpu_util_pct: Optional[float]
    max_memory_gb: Optional[float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duration_s": self.duration_s,
            "request_count": self.request_count,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "avg_power_w": self.avg_power_w,
            "peak_power_w": self.peak_power_w,
            "power_error": self.power_error,
            "energy_j": self.energy_j,
            "energy_wh": self.energy_wh,
            "energy_kwh": self.energy_kwh,
            "joules_per_token": self.joules_per_token,
            "kwh_per_1m_tokens": self.kwh_per_1m_tokens,
            "avg_gpu_util_pct": self.avg_gpu_util_pct,
            "max_memory_gb": self.max_memory_gb,
        }


class SessionStats:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_time = time.monotonic()
        self._last_power_time: Optional[float] = None
        self._last_power_w: Optional[float] = None
        self._power_area_j = 0.0
        self._power_sample_count = 0
        self._power_sum_w = 0.0
        self._peak_power_w: Optional[float] = None
        self._gpu_util_sum = 0.0
        self._gpu_util_count = 0
        self._max_memory_gb: Optional[float] = None
        self._power_error: Optional[str] = None
        self._request_count = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0

    def record_power(
        self,
        total_power_w: float,
        avg_gpu_util_pct: Optional[float],
        max_memory_gb: Optional[float],
    ) -> None:
        now = time.monotonic()
        with self._lock:
            if self._last_power_time is not None and self._last_power_w is not None:
                elapsed_s = max(0.0, now - self._last_power_time)
                self._power_area_j += ((self._last_power_w + total_power_w) / 2.0) * elapsed_s

            self._last_power_time = now
            self._last_power_w = total_power_w
            self._power_sum_w += total_power_w
            self._power_sample_count += 1
            self._peak_power_w = (
                total_power_w
                if self._peak_power_w is None
                else max(self._peak_power_w, total_power_w)
            )

            if avg_gpu_util_pct is not None:
                self._gpu_util_sum += avg_gpu_util_pct
                self._gpu_util_count += 1

            if max_memory_gb is not None:
                self._max_memory_gb = (
                    max_memory_gb
                    if self._max_memory_gb is None
                    else max(self._max_memory_gb, max_memory_gb)
                )

    def set_power_error(self, message: str) -> None:
        with self._lock:
            self._power_error = message

    def record_request(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        with self._lock:
            self._request_count += 1
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._total_tokens += total_tokens or prompt_tokens + completion_tokens

    def snapshot(self) -> SessionSnapshot:
        with self._lock:
            duration_s = max(0.0, time.monotonic() - self._start_time)
            avg_power_w = (
                self._power_sum_w / self._power_sample_count
                if self._power_sample_count
                else None
            )
            tokens_per_second = self._total_tokens / duration_s if duration_s > 0 else None
            joules_per_token = (
                self._power_area_j / self._total_tokens
                if self._total_tokens > 0
                else None
            )
            kwh_per_1m_tokens = (
                joules_per_token * 1_000_000 / 3_600_000
                if joules_per_token is not None
                else None
            )
            avg_gpu_util_pct = (
                self._gpu_util_sum / self._gpu_util_count if self._gpu_util_count else None
            )

            return SessionSnapshot(
                duration_s=duration_s,
                request_count=self._request_count,
                prompt_tokens=self._prompt_tokens,
                completion_tokens=self._completion_tokens,
                total_tokens=self._total_tokens,
                tokens_per_second=tokens_per_second,
                avg_power_w=avg_power_w,
                peak_power_w=self._peak_power_w,
                power_error=self._power_error,
                energy_j=self._power_area_j,
                energy_wh=self._power_area_j / 3600.0,
                energy_kwh=self._power_area_j / 3_600_000.0,
                joules_per_token=joules_per_token,
                kwh_per_1m_tokens=kwh_per_1m_tokens,
                avg_gpu_util_pct=avg_gpu_util_pct,
                max_memory_gb=self._max_memory_gb,
            )
