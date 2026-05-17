# Minimal Validation Plan

This plan keeps the validation burden low while producing enough evidence for a short HPEC paper.

## Claims to Validate

1. The tool can read GPU power telemetry on real NVIDIA hardware.
2. The proxy can connect OpenAI-compatible token usage with GPU power telemetry.
3. The proxy overhead is small enough for deployment-time monitoring.

## Stage 0: GPU Telemetry Check

Run once per machine:

```bash
llm-power-profiler doctor --gpus 0
python3 scripts/collect_env.py --gpus 0 --output reports/env.json
```

Save the GPU model, driver version from `nvidia-smi`, and the `doctor` output screenshot.

## Stage 1: Mock Pipeline Smoke Test

Purpose: verify the software pipeline, not real LLM energy.

Terminal 1:

```bash
python3 examples/mock_openai_server.py --port 8001
```

Terminal 2:

```bash
llm-power-profiler proxy \
  --target http://127.0.0.1:8001 \
  --port 9000 \
  --gpus 0 \
  --interval 0.1 \
  --export reports/mock-profiler.json
```

Terminal 3:

```bash
python3 examples/traffic_generator.py \
  --base-url http://127.0.0.1:9000 \
  --model mock-llm \
  --requests 16 \
  --concurrency 4 \
  --max-tokens 128 \
  --output reports/mock-traffic.jsonl \
  --summary reports/mock-traffic-summary.json
```

Expected:

- `request_count` equals 16.
- `total_tokens` is nonzero.
- `avg_power_w` is nonzero on NVIDIA GPUs.
- active metrics are present in the JSON export.

Or run the automated version:

```bash
python3 scripts/run_mock_validation.py --gpus 0 --prefix mock
```

## Stage 2: One Real vLLM Smoke Run on A100

Terminal 1:

```bash
vllm serve <MODEL_NAME> --port 8001
```

Terminal 2:

```bash
llm-power-profiler proxy \
  --target http://127.0.0.1:8001 \
  --port 9000 \
  --gpus 0 \
  --interval 0.1 \
  --export reports/a100-vllm-profiler.json
```

Terminal 3:

```bash
python3 examples/traffic_generator.py \
  --base-url http://127.0.0.1:9000 \
  --model <MODEL_NAME> \
  --requests 64 \
  --concurrency 4 \
  --max-tokens 256 \
  --output reports/a100-vllm-traffic.jsonl \
  --summary reports/a100-vllm-traffic-summary.json
```

Expected:

- `active_joules_per_token` is nonzero.
- `active_kwh_per_1m_tokens` is nonzero.
- GPU memory reflects model loading.
- average power is higher than the idle mock run.

Automated version, assuming vLLM is already running:

```bash
python3 scripts/run_vllm_validation.py \
  --target http://127.0.0.1:8001 \
  --model <MODEL_NAME> \
  --gpus 0 \
  --prefix a100-vllm
```

## Stage 3: Direct-vs-Proxy Overhead

Run the same traffic directly against the server:

```bash
python3 examples/traffic_generator.py \
  --base-url http://127.0.0.1:8001 \
  --model <MODEL_NAME> \
  --requests 64 \
  --concurrency 4 \
  --max-tokens 256 \
  --output reports/a100-direct-traffic.jsonl \
  --summary reports/a100-direct-traffic-summary.json
```

Compare with the proxied summary:

- `latency_avg_s`
- `latency_p50_s`
- `latency_p95_s`
- `tokens_per_second`

Automated version:

```bash
python3 scripts/run_overhead_validation.py \
  --target http://127.0.0.1:8001 \
  --model <MODEL_NAME> \
  --gpus 0 \
  --prefix a100-overhead
```

## Stage 4: Minimal Cross-GPU Evidence

Repeat Stage 2 on:

- A100
- H100
- H200

Use the same model, prompt, request count, concurrency, and max output tokens.

This is enough for the first HPEC draft figure:

```text
active kWh / 1M tokens across A100, H100, H200
```

## Stage 5: One Small Sweep

Only after Stage 4 works, run:

```text
concurrency = 1, 4, 8
max_tokens = 256
```

This gives the second figure:

```text
active joules/token vs concurrency
```

Automated version:

```bash
python3 scripts/run_concurrency_sweep.py \
  --target http://127.0.0.1:8001 \
  --model <MODEL_NAME> \
  --gpus 0 \
  --concurrency 1,4,8 \
  --prefix a100-vllm
```

Summarize any completed runs:

```bash
python3 scripts/summarize_reports.py --reports-dir reports --csv reports/summary.csv
```
