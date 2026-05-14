from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class NVMLUnavailable(RuntimeError):
    """Raised when NVML cannot be imported or initialized."""


@dataclass(frozen=True)
class GPUSample:
    index: int
    name: str
    power_w: Optional[float]
    utilization_gpu_pct: Optional[float]
    memory_used_gb: Optional[float]
    memory_total_gb: Optional[float]
    temperature_c: Optional[float]


class NVMLMonitor:
    def __init__(self, gpu_indices: Optional[List[int]] = None) -> None:
        try:
            import pynvml
        except Exception as exc:  # pragma: no cover - depends on host GPU setup
            raise NVMLUnavailable("pynvml is not installed or cannot be imported") from exc

        self._pynvml = pynvml
        try:
            pynvml.nvmlInit()
            self._device_count = pynvml.nvmlDeviceGetCount()
        except Exception as exc:  # pragma: no cover - depends on host GPU setup
            raise NVMLUnavailable(f"NVML initialization failed: {exc}") from exc
        self._gpu_indices = gpu_indices or list(range(self._device_count))
        self._validate_gpu_indices()

    def sample(self) -> List[GPUSample]:
        samples: List[GPUSample] = []
        for index in self._gpu_indices:
            handle = self._pynvml.nvmlDeviceGetHandleByIndex(index)
            samples.append(
                GPUSample(
                    index=index,
                    name=self._name(handle),
                    power_w=self._power_w(handle),
                    utilization_gpu_pct=self._utilization_pct(handle),
                    memory_used_gb=self._memory_used_gb(handle),
                    memory_total_gb=self._memory_total_gb(handle),
                    temperature_c=self._temperature_c(handle),
                )
            )
        return samples

    def _validate_gpu_indices(self) -> None:
        invalid = [index for index in self._gpu_indices if index < 0 or index >= self._device_count]
        if invalid:
            raise NVMLUnavailable(
                f"Invalid GPU index {invalid}; available indices are 0-{self._device_count - 1}"
            )

    def _name(self, handle: object) -> str:
        name = self._pynvml.nvmlDeviceGetName(handle)
        return name.decode("utf-8") if isinstance(name, bytes) else str(name)

    def _power_w(self, handle: object) -> Optional[float]:
        try:
            return self._pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
        except Exception:
            return None

    def _utilization_pct(self, handle: object) -> Optional[float]:
        try:
            return float(self._pynvml.nvmlDeviceGetUtilizationRates(handle).gpu)
        except Exception:
            return None

    def _memory_used_gb(self, handle: object) -> Optional[float]:
        try:
            return self._pynvml.nvmlDeviceGetMemoryInfo(handle).used / (1024**3)
        except Exception:
            return None

    def _memory_total_gb(self, handle: object) -> Optional[float]:
        try:
            return self._pynvml.nvmlDeviceGetMemoryInfo(handle).total / (1024**3)
        except Exception:
            return None

    def _temperature_c(self, handle: object) -> Optional[float]:
        try:
            return float(
                self._pynvml.nvmlDeviceGetTemperature(
                    handle,
                    self._pynvml.NVML_TEMPERATURE_GPU,
                )
            )
        except Exception:
            return None


def parse_gpu_indices(value: Optional[str]) -> Optional[List[int]]:
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"", "all"}:
        return None

    indices: List[int] = []
    for part in normalized.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            indices.append(int(part))
        except ValueError as exc:
            raise ValueError(f"Invalid GPU index '{part}'") from exc

    return indices or None
