# HPEC Paper Draft

This directory contains a working IEEE conference paper draft for:

```text
llm-power-profiler: Lightweight Energy-per-Token Monitoring for Local LLM Inference Servers
```

HPEC 2026 submission notes checked on May 14, 2026:

- Full papers are up to 6 pages, with references and acknowledgments not included in that limit.
- Submissions should use the approved IEEE templates.
- The submission deadline is July 7, 2026.

Official pages:

- https://ieee-hpec.org/call-for-papers/
- https://ieee-hpec.org/submit/
- https://ieee-hpec.org/paper-prep/

## Build

If `latexmk` is available:

```bash
make
```

Without `latexmk`:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Drafting Notes

This is intentionally an early skeleton. Replace all `TODO` markers before submission.

Recommended first data to collect:

- A100 mock smoke run, for pipeline validation only.
- A100 vLLM run.
- H100 vLLM run.
- H200 vLLM run.
- Direct-vs-proxy latency overhead.
- Concurrency sweep: 1, 4, 8, 16.
- Output length sweep: 64, 256, 1024.

## IEEE Template Note

The draft uses:

```latex
\documentclass[conference]{IEEEtran}
```

For final submission, verify against the current official IEEE conference template and HPEC instructions.

