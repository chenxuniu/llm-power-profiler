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
    active_tokens_per_second: Optional[float]
    active_duration_s: float
    inflight_requests: int
    avg_power_w: Optional[float]
    peak_power_w: Optional[float]
    power_error: Optional[str]
    energy_j: float
    energy_wh: float
    energy_kwh: float
    joules_per_token: Optional[float]
    kwh_per_1m_tokens: Optional[float]
    active_avg_power_w: Optional[float]
    active_energy_j: float
    active_energy_wh: float
    active_energy_kwh: float
    active_joules_per_token: Optional[float]
    active_kwh_per_1m_tokens: Optional[float]
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
            "active_tokens_per_second": self.active_tokens_per_second,
            "active_duration_s": self.active_duration_s,
            "inflight_requests": self.inflight_requests,
            "avg_power_w": self.avg_power_w,
            "peak_power_w": self.peak_power_w,
            "power_error": self.power_error,
            "energy_j": self.energy_j,
            "energy_wh": self.energy_wh,
            "energy_kwh": self.energy_kwh,
            "joules_per_token": self.joules_per_token,
            "kwh_per_1m_tokens": self.kwh_per_1m_tokens,
            "active_avg_power_w": self.active_avg_power_w,
            "active_energy_j": self.active_energy_j,
            "active_energy_wh": self.active_energy_wh,
            "active_energy_kwh": self.active_energy_kwh,
            "active_joules_per_token": self.active_joules_per_token,
            "active_kwh_per_1m_tokens": self.active_kwh_per_1m_tokens,
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
        self._active_last_time: Optional[float] = None
        self._active_duration_s = 0.0
        self._active_power_area_j = 0.0
        self._active_requests = 0
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
            self._advance_active_window(now)
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

    def begin_request(self) -> None:
        now = time.monotonic()
        with self._lock:
            self._advance_active_window(now)
            self._active_requests += 1
            self._active_last_time = now

    def complete_request(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
    ) -> None:
        now = time.monotonic()
        with self._lock:
            self._advance_active_window(now)
            self._active_requests = max(0, self._active_requests - 1)
            self._active_last_time = now if self._active_requests > 0 else None
            self._request_count += 1
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._total_tokens += total_tokens or prompt_tokens + completion_tokens

    def record_request(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> None:
        with self._lock:
            self._request_count += 1
            self._prompt_tokens += prompt_tokens
            self._completion_tokens += completion_tokens
            self._total_tokens += total_tokens or prompt_tokens + completion_tokens

    def snapshot(self) -> SessionSnapshot:
        now = time.monotonic()
        with self._lock:
            active_duration_s = self._active_duration_s
            active_energy_j = self._active_power_area_j
            if self._active_requests > 0 and self._active_last_time is not None:
                elapsed_s = max(0.0, now - self._active_last_time)
                active_duration_s += elapsed_s
                if self._last_power_w is not None:
                    active_energy_j += self._last_power_w * elapsed_s

            duration_s = max(0.0, now - self._start_time)
            avg_power_w = (
                self._power_sum_w / self._power_sample_count
                if self._power_sample_count
                else None
            )
            tokens_per_second = self._total_tokens / duration_s if duration_s > 0 else None
            active_tokens_per_second = (
                self._total_tokens / active_duration_s if active_duration_s > 0 else None
            )
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
            active_avg_power_w = (
                active_energy_j / active_duration_s if active_duration_s > 0 else None
            )
            active_joules_per_token = (
                active_energy_j / self._total_tokens if self._total_tokens > 0 else None
            )
            active_kwh_per_1m_tokens = (
                active_joules_per_token * 1_000_000 / 3_600_000
                if active_joules_per_token is not None
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
                active_tokens_per_second=active_tokens_per_second,
                active_duration_s=active_duration_s,
                inflight_requests=self._active_requests,
                avg_power_w=avg_power_w,
                peak_power_w=self._peak_power_w,
                power_error=self._power_error,
                energy_j=self._power_area_j,
                energy_wh=self._power_area_j / 3600.0,
                energy_kwh=self._power_area_j / 3_600_000.0,
                joules_per_token=joules_per_token,
                kwh_per_1m_tokens=kwh_per_1m_tokens,
                active_avg_power_w=active_avg_power_w,
                active_energy_j=active_energy_j,
                active_energy_wh=active_energy_j / 3600.0,
                active_energy_kwh=active_energy_j / 3_600_000.0,
                active_joules_per_token=active_joules_per_token,
                active_kwh_per_1m_tokens=active_kwh_per_1m_tokens,
                avg_gpu_util_pct=avg_gpu_util_pct,
                max_memory_gb=self._max_memory_gb,
            )

    def _advance_active_window(self, now: float) -> None:
        if self._active_requests <= 0:
            self._active_last_time = None
            return
        if self._active_last_time is None:
            self._active_last_time = now
            return

        elapsed_s = max(0.0, now - self._active_last_time)
        self._active_duration_s += elapsed_s
        if self._last_power_w is not None:
            self._active_power_area_j += self._last_power_w * elapsed_s
        self._active_last_time = now
