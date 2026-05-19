#!/usr/bin/env bash
# Start the local vLLM OpenAI-compatible server with all speedups enabled.
#
# Reads `llm.server.*` from config/pipeline.yaml — keep this script and
# that block in sync; if you change one, change the other.
#
# Usage:
#   bash scripts/start_vllm_server.sh                 # foreground
#   nohup bash scripts/start_vllm_server.sh \
#         > logs/vllm.log 2>&1 &                       # background
#
# Verify:
#   curl http://localhost:8000/v1/models
#
# Stop:
#   pkill -f "vllm.entrypoints.openai.api_server"

set -euo pipefail

cd "$(dirname "$0")/.."

MODEL="${VLLM_MODEL:-deepseek-ai/DeepSeek-R1-Distill-Qwen-14B}"
HOST="${VLLM_HOST:-0.0.0.0}"
PORT="${VLLM_PORT:-8000}"
DTYPE="${VLLM_DTYPE:-bfloat16}"
GPU_UTIL="${VLLM_GPU_UTIL:-0.88}"
MAX_LEN="${VLLM_MAX_MODEL_LEN:-16384}"
ATTN_BACKEND="${VLLM_ATTENTION_BACKEND:-FLASH_ATTN}"
SWAP_GB="${VLLM_SWAP_SPACE:-4}"
TP="${VLLM_TENSOR_PARALLEL:-1}"

# vLLM picks up VLLM_ATTENTION_BACKEND from env.
export VLLM_ATTENTION_BACKEND="$ATTN_BACKEND"
# Allow HF to fetch the model the first time; cache lives in HF_HOME.
export HF_HOME="${HF_HOME:-$PWD/.hf_cache}"
mkdir -p "$HF_HOME" logs

echo "[start_vllm_server] model            = $MODEL"
echo "[start_vllm_server] host:port        = $HOST:$PORT"
echo "[start_vllm_server] dtype            = $DTYPE"
echo "[start_vllm_server] gpu_mem_util     = $GPU_UTIL"
echo "[start_vllm_server] max_model_len    = $MAX_LEN"
echo "[start_vllm_server] attention_backend= $ATTN_BACKEND"
echo "[start_vllm_server] tensor_parallel  = $TP"
echo "[start_vllm_server] HF_HOME          = $HF_HOME"

exec uv run python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL" \
    --host "$HOST" \
    --port "$PORT" \
    --dtype "$DTYPE" \
    --gpu-memory-utilization "$GPU_UTIL" \
    --max-model-len "$MAX_LEN" \
    --tensor-parallel-size "$TP" \
    --swap-space "$SWAP_GB" \
    --enable-prefix-caching \
    --enable-chunked-prefill \
    --trust-remote-code \
    --disable-log-requests
