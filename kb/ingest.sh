#!/usr/bin/env bash
# Build the CareGuard knowledge base.
#
#   ./kb/ingest.sh            # fetch public docs + build the BM25 index (no GPU needed)
#   ./kb/ingest.sh --chroma   # ...and embed into ChromaDB with Ollama nomic-embed-text
#   ./kb/ingest.sh --itu PATH # ...or ingest with the unmodified ITU AI Readiness reference code
#                             #    (PATH = your clone of github.com/CrashingGuru/ITUAIReadiness)
set -euo pipefail
cd "$(dirname "$0")/.."

python kb/fetch_docs.py
python kb/build_index.py

case "${1:-}" in
  --chroma)
    python kb/ingest_chroma.py --reset
    ;;
  --itu)
    ITU="${2:?usage: kb/ingest.sh --itu /path/to/ITUAIReadiness}"
    DEST="$ITU/simulation/server/knowledge/InputDocs/CareGuard_UAE_Health"
    mkdir -p "$DEST"
    # The reference ingest treats each first-level folder as a document_category,
    # so all CareGuard documents go into one category folder.
    find kb/InputDocs -type f \( -name '*.pdf' -o -name '*.html' -o -name '*.txt' -o -name '*.md' \) -exec cp {} "$DEST"/ \;
    (cd "$ITU/simulation" && python -m server.knowledge.ingest --reset)
    ;;
esac
