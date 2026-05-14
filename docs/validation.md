# Validation Guide

This guide is for validating `llm-power-profiler` on a local machine before trying a full GPU/vLLM setup.

## 1. Start the Mock Server

```bash
python3 examples/mock_openai_server.py
```

The mock server listens on:

```text
http://127.0.0.1:8000
```

## 2. Start the Profiler Proxy

In another terminal:

```bash
llm-power-profiler proxy \
  --target http://127.0.0.1:8000 \
  --port 9000 \
  --gpus 0 \
  --export reports/mock-session.json
```

If NVML is unavailable, token metrics still work and power metrics are shown as disabled.

## 3. Send a Test Request

```bash
curl http://127.0.0.1:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mock-llm",
    "messages": [{"role": "user", "content": "Explain joules per token briefly."}],
    "max_tokens": 32
  }'
```

Stop the proxy with `Ctrl-C`. The JSON report is written to:

```text
reports/mock-session.json
```

You can also generate repeatable test traffic:

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

## 4. Validate with vLLM

Start vLLM:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

Start the profiler:

```bash
llm-power-profiler proxy \
  --target http://127.0.0.1:8000 \
  --port 9000 \
  --gpus 0 \
  --export reports/vllm-session.json
```

Send traffic to:

```text
http://127.0.0.1:9000/v1/chat/completions
```

Expected result:

- requests increase
- prompt/completion/total tokens increase
- GPU average and peak power show values on NVIDIA systems
- joules per token becomes non-empty after both power and token data are present
