# Design

`llm-power-profiler` is designed as a lightweight local monitor, not a benchmark suite.

The core loop is:

```text
OpenAI-compatible client
  -> llm-power-profiler proxy
  -> local LLM server
  -> response usage.total_tokens

NVML sampler
  -> GPU watts/utilization/memory

Stats engine
  -> joules per token
  -> kWh per 1M tokens
  -> terminal dashboard
```

## Principles

- Stay local-first.
- Require no root privileges.
- Depend on NVML instead of DCGM for the first version.
- Treat token usage as an application-layer signal.
- Treat GPU power as a node-level telemetry signal.
- Report aggregate session metrics before attempting request-level attribution.

## Modules

- `cli.py`: Typer command entrypoints.
- `doctor.py`: environment and telemetry checks.
- `nvml.py`: NVIDIA GPU sampling through NVML.
- `proxy.py`: OpenAI-compatible HTTP forwarding and usage extraction.
- `stats.py`: thread-safe counters and energy integration.
- `tui.py`: Rich terminal rendering.

## First-Version Assumptions

- The local LLM server returns OpenAI-style JSON responses.
- The response includes `usage.total_tokens`.
- Non-streaming responses are used for token accounting.
- Total GPU power is attributed to the session as an aggregate estimate.

## Later Extensions

- Streaming token accounting.
- JSON/CSV session export.
- Per-request approximate attribution windows.
- vLLM metrics endpoint integration.
- Prometheus exporter.
- DCGM backend.
- Slurm job metadata.
- Multi-node aggregation.

