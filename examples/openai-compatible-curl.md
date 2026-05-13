# OpenAI-Compatible curl Example

Any local server that returns an OpenAI-style `usage` object can be monitored.

```json
{
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 64,
    "total_tokens": 76
  }
}
```

Run:

```bash
llm-power-profiler proxy --target http://localhost:8000 --port 9000
```

Then point your client to:

```text
http://localhost:9000/v1/chat/completions
```

