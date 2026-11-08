"""Embed the CareGuard chunks into ChromaDB with Ollama nomic-embed-text.

This is the GPU/LLM path, compatible with the ITU AI Readiness reference stack
(https://github.com/CrashingGuru/ITUAIReadiness, simulation/server/knowledge):
same embedding model (nomic-embed-text), same vector store (ChromaDB), same
collection name (kb_main) and the same metadata keys the reference ingest writes
(source_file, source_type, country, chunk_index, total_chunks, document_category),
plus doc_id / title / page for page-level source attribution.

Prerequisites:
    pip install chromadb ollama
    ollama pull nomic-embed-text
    python kb/build_index.py          # produces kb/index/chunks.jsonl

Usage:
    python kb/ingest_chroma.py [--reset] [--persist kb/chroma] [--host http://localhost:11434]

To ingest the same documents with the unmodified ITU reference code instead, see kb/ingest.sh.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

KB = Path(__file__).resolve().parent

SOURCE_TYPE = {  # map manifest "type" to the ITU reference source_type vocabulary
    "national_strategy": "national_strategy", "policy_document": "policy_document",
    "legislation": "policy_document", "regulation": "policy_document", "standard": "standards_document",
    "standards_document": "standards_document", "protocol": "policy_document", "guideline": "policy_document",
    "guidance": "policy_document", "treaty": "policy_document",
    "international_org_report": "international_org_report",
}


def main() -> None:
    import chromadb
    import ollama
    import yaml

    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--persist", default=str(KB / "chroma"))
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    manifest = {d["id"]: d for d in yaml.safe_load((KB / "manifest.yaml").read_text())["documents"]}
    chunks = [json.loads(l) for l in (KB / "index" / "chunks.jsonl").read_text().splitlines() if l.strip()]
    totals = Counter(c["doc_id"] for c in chunks)

    client = chromadb.PersistentClient(path=args.persist)
    if args.reset:
        try:
            client.delete_collection("kb_main")
        except Exception:  # noqa: BLE001
            pass
    col = client.get_or_create_collection("kb_main", metadata={"hnsw:space": "cosine"})
    emb = ollama.Client(host=args.host)

    for i in range(0, len(chunks), args.batch):
        batch = chunks[i:i + args.batch]
        vecs = emb.embed(model=args.model, input=[c["text"][:2000] for c in batch])["embeddings"]
        metas = []
        for c in batch:
            m = manifest[c["doc_id"]]
            metas.append({
                "source_file": Path(c["file"]).name,
                "source_type": SOURCE_TYPE.get(m["type"], "international_org_report"),
                "country": m["jurisdiction"],
                "chunk_index": str(c["chunk_index"]),
                "total_chunks": str(totals[c["doc_id"]]),
                "document_category": c["file"].split("/")[0],
                "doc_id": c["doc_id"], "title": c["title"], "page": c["page"], "source_url": m["url"],
            })
        col.upsert(ids=[c["chunk_id"] for c in batch], documents=[c["text"] for c in batch],
                   embeddings=vecs, metadatas=metas)
        print(f"  embedded {min(i + args.batch, len(chunks))}/{len(chunks)}", end="\r")
    print(f"\nkb_main now holds {col.count()} chunks in {args.persist}")


if __name__ == "__main__":
    main()
