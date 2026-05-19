#!/usr/bin/env bash
# Phase-12 post-processing — to run after `scripts/run_demo.py --all`
# completes the real-LLM pipeline. Refreshes every Phase-12 artifact
# against the real traces in manuscript/traces_real/.
#
# Steps:
#   1. eval_ablations.py — Tables 4 + 5 (4-condition, real LLM)
#                          (condition (d) reuses cached real-LLM traces)
#   2. sensitivity_sweep.py — Fig 9 + Fig 12 data
#   3. provenance_audit.py — Table 6 (against real assertions)
#   4. render_figures.py   — Figs 7, 8, 9, 11, 12 SVGs
#
# Estimated wall-clock: ~10–15 minutes for the eval_ablations real-LLM
# calls (only conditions (a)/(b)/(c) make new LLM calls; (d) is reused).
# Everything else is pure Python in seconds.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/root/.local/bin:$PATH"
export HF_HOME="${HF_HOME:-$PWD/.hf_cache}"

echo "[postprocess] (1/4) eval_ablations.py (real LLM, reusing traces_real/) ..."
uv run python scripts/eval_ablations.py \
    --reuse-traces-from manuscript/traces_real

echo "[postprocess] (2/4) sensitivity_sweep.py ..."
uv run python scripts/sensitivity_sweep.py

echo "[postprocess] (3/4) provenance_audit.py (traces_real/) ..."
uv run python scripts/provenance_audit.py --traces-dir manuscript/traces_real

echo "[postprocess] (4/4) render_figures.py (traces_real/) ..."
uv run python scripts/render_figures.py --traces-dir manuscript/traces_real

echo "[postprocess] DONE."
echo "  Tables:  manuscript/tables_draft/table{4,5,6}_*.{md,tex}"
echo "  Figures: manuscript/figures/fig{7,8,9,11,12}_*.svg"
echo "  Data:    manuscript/data/{ablation_metrics,sensitivity_*,provenance_audit}.json"
