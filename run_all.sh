#!/usr/bin/env bash
# Rebuild the KB index, run all three scenarios and regenerate the gap report.
#   BACKEND=auto RETRIEVER=auto ./run_all.sh   # use Ollama/Chroma when available
set -euo pipefail
cd "$(dirname "$0")"
[ -f kb/index/chunks.jsonl ] || python kb/build_index.py
python coordinator/run_scenario.py scenarios/A_dropped_meds.yaml scenarios/B_voice_offshore.yaml scenarios/C_consent.yaml \
  --backend "${BACKEND:-rules}" --retriever "${RETRIEVER:-bm25}"
python coordinator/gap_report.py
