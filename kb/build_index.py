"""Parse kb/InputDocs into page-aware chunks for the lightweight (no GPU) retriever.

Output: kb/index/chunks.jsonl, one JSON object per chunk:
  {chunk_id, doc_id, title, jurisdiction, authority, file, page, chunk_index, text}

Chunking follows the ITU AI Readiness reference settings (chunk_size=256 words,
overlap=30 words) but is done per page so every chunk keeps a page number for
source attribution. HTML sources have no pages; they are split into ~600-word
sections and the section number is reported as the "page". Image-only PDF pages
are OCR'd with tesseract when it is installed.

Usage:  python kb/build_index.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import yaml

KB = Path(__file__).resolve().parent
DOCS = KB / "InputDocs"
OUT = KB / "index"
CHUNK_WORDS = 256
OVERLAP = 30
HTML_SECTION_WORDS = 600


def pdf_pages(path: Path) -> list[str]:
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24
    except ImportError:  # pragma: no cover
        import fitz
    pages = []
    with fitz.open(str(path)) as doc:
        for p in doc:
            txt = p.get_text()
            if len(txt.strip()) < 50:  # image-only page: OCR fallback with tesseract (if installed)
                txt = ocr_page(p) or txt
            pages.append(txt)
    return pages


def ocr_page(page) -> str:
    import shutil, subprocess, tempfile
    if not shutil.which("tesseract"):
        return ""
    with tempfile.TemporaryDirectory() as td:
        png = Path(td) / "p.png"
        page.get_pixmap(dpi=200).save(str(png))
        r = subprocess.run(["tesseract", str(png), "-", "-l", "eng"], capture_output=True, text=True)
        return r.stdout


def html_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def html_pages(path: Path) -> list[str]:
    words = html_text(path).split()
    return [" ".join(words[i:i + HTML_SECTION_WORDS]) for i in range(0, len(words), HTML_SECTION_WORDS)]


def chunk_words(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    out, step = [], CHUNK_WORDS - OVERLAP
    for i in range(0, len(words), step):
        piece = words[i:i + CHUNK_WORDS]
        if len(piece) < 25 and out:  # tiny tail: merge into previous chunk
            out[-1] += " " + " ".join(piece)
            break
        out.append(" ".join(piece))
        if i + CHUNK_WORDS >= len(words):
            break
    return out


def main() -> int:
    manifest = yaml.safe_load((KB / "manifest.yaml").read_text())
    OUT.mkdir(exist_ok=True)
    n_docs = n_chunks = 0
    stats = []
    with open(OUT / "chunks.jsonl", "w", encoding="utf-8") as f:
        for d in manifest["documents"]:
            path = DOCS / d["file"]
            if not path.exists():
                stats.append((d["id"], "missing", 0, 0))
                continue
            pages = pdf_pages(path) if path.suffix.lower() == ".pdf" else html_pages(path)
            k = 0
            for pno, ptxt in enumerate(pages, start=1):
                for c in chunk_words(ptxt):
                    rec = {
                        "chunk_id": f"{d['id']}#p{pno}c{k}",
                        "doc_id": d["id"], "title": d["title"],
                        "jurisdiction": d["jurisdiction"], "authority": d["authority"],
                        "file": d["file"], "page": pno, "chunk_index": k, "text": c,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    k += 1
            n_docs += 1
            n_chunks += k
            stats.append((d["id"], "indexed", len(pages), k))
    for s in stats:
        print(f"{s[1]:8s} {s[0]:38s} pages={s[2]:<5} chunks={s[3]}")
    print(f"\nIndexed {n_docs} documents into {n_chunks} chunks -> {OUT / 'chunks.jsonl'}")
    (OUT / "index_stats.json").write_text(json.dumps(
        [{"doc_id": a, "status": b, "pages": c, "chunks": e} for a, b, c, e in stats], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
