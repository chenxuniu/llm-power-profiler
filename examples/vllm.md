# vLLM Example

Start vLLM:

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

Start the profiler proxy:

```bash
llm-power-profiler proxy --target http://localhost:8000 --port 9000
```

Send requests to the profiler:

```bash
curl http://localhost:9000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "What is joules per token?"}],
    "max_tokens": 128
  }'
```

