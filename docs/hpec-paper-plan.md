# HPEC Paper Plan

Working title:

```text
llm-power-profiler: Lightweight Energy-per-Token Monitoring for Local LLM Inference Servers
```

## Positioning

This is a short systems/tool paper, not a full benchmark-suite paper.

The central claim:

```text
Deployment-time LLM energy observability can be made lightweight by bridging
OpenAI-compatible token usage with NVML GPU power telemetry.
```

## Motivation

Existing tools expose pieces of the problem:

- `nvidia-smi` exposes GPU power, utilization, memory, and temperature.
- LLM serving systems expose token usage and throughput.
- Benchmark suites provide controlled evaluation, but are often too heavy for daily local deployment monitoring.

The gap:

```text
Engineers need a low-friction way to observe joules per token while a local LLM
server is already running.
```

## Contributions

1. A lightweight proxy-based method for connecting LLM token usage with GPU power telemetry.
2. An open-source implementation for OpenAI-compatible local inference servers.
3. An evaluation across A100, H100, and H200 systems showing how joules/token changes with concurrency, output length, and model/server configuration.

## System Design

The tool sits between an OpenAI-compatible client and server:

```text
client -> llm-power-profiler proxy -> vLLM/SGLang/TGI/Ollama-compatible server
```

It collects:

- application-layer token usage from response `usage`
- system-layer power telemetry from NVML
- aggregate session-level energy-per-token metrics

## Evaluation Questions

1. Can the proxy collect useful energy-per-token metrics without modifying the LLM server?
2. What is the proxy overhead compared with direct requests?
3. How do concurrency and output length affect joules/token?
4. How do A100, H100, and H200 compare under the same workload shape?
5. Are the observed trends stable enough to guide deployment decisions?

## Initial Experiment Matrix

Hardware:

- A100
- H100
- H200

Serving stack:

- vLLM first
- SGLang optional

Models:

- one 7B/8B model for initial runs
- one larger model if resources allow

Concurrency:

- 1
- 4
- 8
- 16

Max output tokens:

- 64
- 256
- 1024

## Key Figures

- `joules/token` vs concurrency
- `tokens/sec` vs average GPU power
- `kWh/1M tokens` across A100, H100, and H200
- proxy overhead, measured as direct latency vs proxied latency
- energy breakdown by output length

## Paper Structure

1. Introduction
2. Background and Motivation
3. Design
4. Implementation
5. Experimental Methodology
6. Evaluation
7. Limitations
8. Conclusion

## Limitations to State Clearly

- Session-level attribution, not exact per-request energy accounting.
- GPU power only in the first version; CPU/DRAM/network power are not included.
- Non-streaming token accounting in the initial implementation.
- NVML power telemetry sampling has finite resolution.
- Multi-tenant GPU usage can distort attribution.

