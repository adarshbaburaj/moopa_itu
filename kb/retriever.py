"""Retrieval backends for CareGuard agents.

* BM25Retriever   : pure-Python Okapi BM25 over kb/index/chunks.jsonl. No GPU, no network.
* ChromaRetriever : ChromaDB collection built by kb/ingest_chroma.py with Ollama
                    nomic-embed-text embeddings (same stack as the ITU AI Readiness
                    reference code).

get_retriever("auto") returns ChromaRetriever when chromadb, ollama and a populated
collection are all available, otherwise BM25Retriever.

Every hit is a dict: {chunk_id, doc_id, title, file, page, score, text, backend}.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

KB = Path(__file__).resolve().parent
INDEX = KB / "index" / "chunks.jsonl"

_STOP = set("""a an the and or of to in on for by with as at from is are be been being this that these those
it its into such any all shall may must not no which who whom whose their there than then so if
under per via within without upon other others also has have had was were will would can could
article section state law decree federal""".split())
_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    toks = [t for t in _TOKEN.findall(text.lower()) if t not in _STOP and len(t) > 1]
    # light stemming so "devices"/"device", "consented"/"consent" match
    out = []
    for t in toks:
        for suf in ("ations", "ation", "ings", "ing", "ies", "es", "ed", "s"):
            if len(t) > len(suf) + 3 and t.endswith(suf):
                t = t[: -len(suf)] + ("y" if suf == "ies" else "")
                break
        out.append(t)
    return out


class BM25Retriever:
    name = "bm25"

    def __init__(self, index_path: Path = INDEX, k1: float = 1.5, b: float = 0.75):
        if not index_path.exists():
            raise FileNotFoundError(f"{index_path} not found. Run: python kb/build_index.py")
        self.chunks = [json.loads(l) for l in index_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.k1, self.b = k1, b
        self.tf: list[Counter] = []
        df: Counter = Counter()
        for c in self.chunks:
            tf = Counter(tokenize(c["title"] + " " + c["text"]))
            self.tf.append(tf)
            df.update(tf.keys())
        self.N = len(self.chunks)
        self.avgdl = sum(sum(t.values()) for t in self.tf) / max(self.N, 1)
        self.idf = {t: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
        self.postings: dict[str, list[int]] = defaultdict(list)
        for i, tf in enumerate(self.tf):
            for t in tf:
                self.postings[t].append(i)

    def search(self, query: str, k: int = 5, doc_ids: list[str] | None = None) -> list[dict]:
        q = tokenize(query)
        scores: dict[int, float] = defaultdict(float)
        allowed = set(doc_ids) if doc_ids else None
        for t in set(q):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i in self.postings[t]:
                if allowed and self.chunks[i]["doc_id"] not in allowed:
                    continue
                tf = self.tf[i][t]
                dl = sum(self.tf[i].values())
                scores[i] += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        best = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
        return [self._hit(i, s) for i, s in best]

    def _hit(self, i: int, s: float) -> dict:
        c = self.chunks[i]
        return {"chunk_id": c["chunk_id"], "doc_id": c["doc_id"], "title": c["title"], "file": c["file"],
                "page": c["page"], "score": round(s, 3), "text": c["text"], "backend": self.name}


class ChromaRetriever:
    name = "chroma+nomic-embed-text"

    def __init__(self, persist_dir: Path = KB / "chroma", collection: str = "kb_main",
                 embed_model: str = "nomic-embed-text", host: str = "http://localhost:11434"):
        import chromadb  # noqa: F401
        import ollama
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.col = self.client.get_collection(collection)
        if self.col.count() == 0:
            raise RuntimeError("Chroma collection is empty. Run kb/ingest_chroma.py")
        self.ollama = ollama.Client(host=host)
        self.embed_model = embed_model

    def search(self, query: str, k: int = 5, doc_ids: list[str] | None = None) -> list[dict]:
        emb = self.ollama.embed(model=self.embed_model, input=[query])["embeddings"][0]
        where = {"doc_id": {"$in": doc_ids}} if doc_ids else None
        r = self.col.query(query_embeddings=[emb], n_results=k, where=where)
        hits = []
        for cid, doc, meta, dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0]):
            hits.append({"chunk_id": cid, "doc_id": meta.get("doc_id"), "title": meta.get("title"),
                         "file": meta.get("source_file"), "page": int(meta.get("page", 0)),
                         "score": round(1 - float(dist), 3), "text": doc, "backend": self.name})
        return hits


def get_retriever(backend: str = "auto"):
    if backend in ("auto", "chroma"):
        try:
            return ChromaRetriever()
        except Exception as e:  # noqa: BLE001
            if backend == "chroma":
                raise
            print(f"[retriever] Chroma/Ollama unavailable ({type(e).__name__}: {e}); using BM25 fallback")
    return BM25Retriever()


if __name__ == "__main__":
    import sys
    r = get_retriever(sys.argv[2] if len(sys.argv) > 2 else "bm25")
    for h in r.search(sys.argv[1] if len(sys.argv) > 1 else "health data stored outside the State", k=5):
        print(f"{h['score']:7.3f}  {h['doc_id']:34s} p{h['page']:<4} {h['text'][:110]!r}")
