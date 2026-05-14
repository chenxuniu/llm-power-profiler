# Experiment Plan

This page tracks the first paper-oriented experiments for `llm-power-profiler`.

## Goal

Measure whether a lightweight local proxy can provide useful deployment-time energy-per-token signals for OpenAI-compatible LLM inference servers.

## Hardware Matrix

Start with the resources available now:

| System | GPU | Role |
| --- | --- | --- |
| Local workstation | A100 | development, smoke tests, first plots |
| Cluster node | H100 | primary evaluation |
| Cluster node | H200 | architecture comparison |

## Serving Stack

First target:

- vLLM OpenAI-compatible server

Optional later targets:

- SGLang
- TGI
- llama.cpp server
- Ollama OpenAI-compatible endpoint

## Workloads

For each GPU/server/model configuration:

- concurrency: 1, 4, 8, 16
- max output tokens: 64, 256, 1024
- request count: at least 64 per setting for smoke runs, more for final plots
- prompts: fixed prompt set first, then mixed prompt lengths

## Metrics

From `llm-power-profiler`:

- total tokens
- tokens/sec
- average power
- peak power
- energy kWh
- joules/token
- kWh/1M tokens

From the traffic generator:

- request count
- completed requests
- error count
- average latency
- p50 latency
- p95 latency

## First Smoke Run

Terminal 1:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

Terminal 2:

```bash
llm-power-profiler proxy \
  --target http://127.0.0.1:8000 \
  --port 9000 \
  --gpus 0 \
  --export reports/a100-vllm-smoke-profiler.json
```

Terminal 3:

```bash
python3 examples/traffic_generator.py \
  --base-url http://127.0.0.1:9000 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --requests 64 \
  --concurrency 4 \
  --max-tokens 256 \
  --output reports/a100-vllm-smoke-traffic.jsonl \
  --summary reports/a100-vllm-smoke-traffic-summary.json
```

Stop the proxy with `Ctrl-C` after the traffic generator finishes.

## Direct-vs-Proxy Overhead Run

Run the same traffic twice:

1. Directly against the serving endpoint, for example `http://127.0.0.1:8000`.
2. Through the profiler proxy, for example `http://127.0.0.1:9000`.

Example direct run:

```bash
python3 examples/traffic_generator.py \
  --base-url http://127.0.0.1:8000 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --requests 64 \
  --concurrency 4 \
  --max-tokens 256 \
  --output reports/a100-vllm-direct-traffic.jsonl \
  --summary reports/a100-vllm-direct-traffic-summary.json
```

Compare `latency_avg_s`, `latency_p50_s`, and `latency_p95_s` with the proxied run.

## Paper Figures

Likely first figures:

- joules/token vs concurrency
- tokens/sec vs average power
- kWh/1M tokens across A100, H100, H200
- proxy overhead vs direct server request latency

## Minimal Paper Path

To keep the first paper iteration lightweight, prioritize:

1. one A100 vLLM run to prove real inference monitoring;
2. one direct-vs-proxy overhead run on A100;
3. one matched H100 run;
4. one matched H200 run;
5. a small concurrency sweep only after the single-point runs work.

Use `active_joules_per_token` and `active_kwh_per_1m_tokens` as the primary energy metrics for paper figures, because session-level metrics include idle time before and after traffic.
