# Contributing

Thanks for your interest in `llm-power-profiler`.

The project is intentionally lightweight. Before adding a feature, ask whether it helps a local LLM user answer one of these questions:

- How many watts is my LLM server using?
- How many tokens did it serve?
- How many joules per token did this session consume?

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

```bash
python3 -m compileall src tests examples
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Scope

Good first contributions:

- Better OpenAI-compatible usage parsing.
- JSON/CSV export improvements.
- vLLM, SGLang, TGI, llama.cpp, and Ollama examples.
- More helpful NVML error messages.
- Terminal UI polish.

Please keep heavyweight integrations optional.

