# Roadmap

## v0.1.0: Local Proxy MVP

- OpenAI-compatible proxy
- aggregate token accounting from `usage`
- NVML power sampling
- terminal dashboard
- JSON session export
- mock OpenAI-compatible server
- GPU selection with `--gpus`

## v0.2.0: Real Server Recipes

- verified vLLM recipe
- SGLang recipe
- TGI recipe
- llama.cpp server recipe
- Ollama OpenAI-compatible recipe
- A100/H100/H200 experiment recipes

## v0.3.0: Better Reporting

- CSV export
- per-endpoint counters
- approximate per-request attribution windows
- HTML report
- screenshots and examples for README

## Later

- streaming token accounting
- Prometheus exporter
- DCGM backend
- Slurm job metadata
- multi-node aggregation
