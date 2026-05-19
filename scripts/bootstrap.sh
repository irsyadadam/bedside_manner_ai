#!/usr/bin/env bash
# scripts/bootstrap.sh
#
# Reproduce the entire ingest pipeline on a fresh checkout. Runs
# Phases 2 → 6 in order and exits. The result is a fully populated
# db/ + index/chroma/ + db/manifest.jsonl + corpus summary in README.
#
# After this finishes you can:
#   - uv run python scripts/run_demo.py --demo --all                 (mock)
#   - bash scripts/start_vllm_server.sh && \
#     uv run python scripts/run_demo.py --all                        (real)
#
# Usage:
#   bash scripts/bootstrap.sh                # full ingest, ~10 min
#   bash scripts/bootstrap.sh --skip-index   # skip Phase 5 (no GPU)
#   bash scripts/bootstrap.sh --resume       # idempotent re-run
#
# Required: uv installed (https://docs.astral.sh/uv/), Python 3.11.
# Optional: NCBI_API_KEY env var (10 req/s vs 3 req/s default),
#           CUDA-capable GPU (Phase 5 falls back to CPU otherwise).
#
# This script is idempotent — every phase already skips work that's
# already done, so a partial bootstrap can be resumed by re-running.

set -euo pipefail

SKIP_INDEX=0
for arg in "$@"; do
    case "$arg" in
        --skip-index)  SKIP_INDEX=1 ;;
        --resume)      ;;  # default behavior; flag is just documentation
        *)             echo "[bootstrap] unknown arg: $arg" ; exit 2 ;;
    esac
done

cd "$(dirname "$0")/.."

# Load .env if present (NCBI_API_KEY, NCBI_EMAIL, HF_TOKEN, ...)
if [[ -f .env ]]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

echo "================================================================"
echo "[bootstrap] clinicomm reproduction — phases 2 through 6"
echo "================================================================"
echo "  cwd:           $(pwd)"
echo "  NCBI_API_KEY:  ${NCBI_API_KEY:+set}${NCBI_API_KEY:-(unset; 3 req/s)}"
echo "  NCBI_EMAIL:    ${NCBI_EMAIL:-(falling back to config/pipeline.yaml)}"
echo "  HF_HOME:       ${HF_HOME:-$(pwd)/.hf_cache}"
echo "  SKIP_INDEX:    ${SKIP_INDEX}"
echo

# uv sync — install all Python deps (no-op if already synced)
echo "[bootstrap] (0/5) uv sync ..."
uv sync >/dev/null
echo "    done."
echo

# Phase 2: PubMed discovery (ESearch + ESummary)
echo "[bootstrap] (1/5) Phase 2 — PubMed discovery (ESearch + ESummary) ..."
uv run python -m clinicomm.ingest.discovery
echo

# Phase 3: full-record fetch (EFetch) + normalize
echo "[bootstrap] (2/5) Phase 3 — EFetch XML + normalize to JSON ..."
uv run python -m clinicomm.ingest.efetch
echo

# Phase 4: chunking
echo "[bootstrap] (3/5) Phase 4 — chunking abstracts ..."
uv run python -m clinicomm.embed.chunk
echo

# Phase 5: embedding + Chroma index
if [[ "$SKIP_INDEX" -eq 1 ]]; then
    echo "[bootstrap] (4/5) Phase 5 — SKIPPED via --skip-index."
    echo "             You can run it later with:"
    echo "               uv run python -m clinicomm.embed.build_index"
else
    echo "[bootstrap] (4/5) Phase 5 — BGE embedding + Chroma index ..."
    echo "             (first run downloads BAAI/bge-large-en-v1.5 ~ 1.3 GB)"
    uv run python -m clinicomm.embed.build_index
fi
echo

# Phase 6: manifest + README corpus summary refresh
echo "[bootstrap] (5/5) Phase 6 — manifest + README corpus summary ..."
uv run python -m clinicomm.ingest.manifest
echo

echo "================================================================"
echo "[bootstrap] DONE."
echo "  next steps:"
echo "    Mock end-to-end demo (no GPU):"
echo "      uv run python scripts/run_demo.py --demo --all"
echo
echo "    Real LLM (requires NVIDIA driver supporting CUDA 12.4+):"
echo "      bash scripts/start_vllm_server.sh &"
echo "      uv run python scripts/run_demo.py --all"
echo
echo "    Generate manuscript artifacts (figures already committed):"
echo "      uv run python scripts/gen_manuscript_artifacts.py --demo"
echo "================================================================"
