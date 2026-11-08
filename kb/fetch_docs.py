"""Download the public documents listed in kb/manifest.yaml into kb/InputDocs.

Writes kb/fetch_status.json with, for every document, whether it was fetched,
its size, sha256 and the HTTP outcome. Documents that cannot be downloaded
(blocked, paywalled, moved) are marked "pending" and are simply skipped by the
ingest step; the manifest still records their source URL.

Usage:  python kb/fetch_docs.py [--force]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

KB = Path(__file__).resolve().parent
DOCS = KB / "InputDocs"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")


def looks_ok(data: bytes, expect_pdf: bool) -> tuple[bool, str]:
    if len(data) < 2000:
        return False, f"too small ({len(data)} bytes)"
    head = data[:2048].lower()
    if expect_pdf:
        if data[:5] != b"%PDF-":
            return False, "expected PDF but got non-PDF content (likely a block page)"
        return True, "pdf"
    if b"<html" not in head and b"<!doctype" not in head:
        return False, "expected HTML"
    if re.search(rb"access denied|captcha|request blocked|cf-challenge", data[:20000], re.I):
        return False, "block / challenge page"
    return True, "html"


def _intermediate_bundle(host: str) -> str | None:
    """Some government servers omit their intermediate certificate. Fetch it via the
    leaf certificate's AIA 'CA Issuers' URL and build a CA bundle that still verifies
    the full chain (verification is never disabled)."""
    import subprocess, tempfile
    try:
        leaf = subprocess.run(["openssl", "s_client", "-connect", f"{host}:443", "-servername", host],
                              input=b"", capture_output=True, timeout=30).stdout
        m = re.search(rb"-----BEGIN CERTIFICATE-----.+?-----END CERTIFICATE-----", leaf, re.S)
        if not m:
            return None
        aia = subprocess.run(["openssl", "x509", "-noout", "-ext", "authorityInfoAccess"],
                             input=m.group(0), capture_output=True, timeout=10).stdout.decode()
        url = re.search(r"CA Issuers - URI:(\S+)", aia)
        if not url:
            return None
        try:
            der = urllib.request.urlopen(urllib.request.Request(url.group(1), headers={"User-Agent": UA}), timeout=30).read()
        except Exception:  # noqa: BLE001  (some proxies mangle plain-http requests from urllib; fall back to curl)
            der = subprocess.run(["curl", "-sfL", "--max-time", "30", url.group(1)], capture_output=True).stdout
        pem = subprocess.run(["openssl", "x509", "-inform", "DER" if not der.startswith(b"-----") else "PEM"],
                             input=der, capture_output=True, timeout=10).stdout
        bundle = tempfile.NamedTemporaryFile("wb", suffix=".pem", delete=False)
        bundle.write(Path(ssl.get_default_verify_paths().cafile or "/etc/ssl/certs/ca-certificates.crt").read_bytes())
        bundle.write(b"\n" + pem)
        bundle.close()
        return bundle.name
    except Exception:  # noqa: BLE001
        return None


def fetch(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            return r.read()
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        host = urllib.parse.urlparse(url).hostname
        cafile = _intermediate_bundle(host)
        if not cafile:
            raise
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context(cafile=cafile)) as r:
            return r.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    manifest = yaml.safe_load((KB / "manifest.yaml").read_text())
    status = {}
    for d in manifest["documents"]:
        target = DOCS / d["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        expect_pdf = target.suffix.lower() == ".pdf"
        rec = {"title": d["title"], "url": d["url"], "file": d["file"]}
        if target.exists() and not args.force:
            data = target.read_bytes()
            rec.update(status="fetched", note="already present")
        else:
            data = b""
            last_err = ""
            for url in [d["url"]] + [d[k] for k in ("mirror_url", "mirror_url_2", "alt_url") if d.get(k)]:
                try:
                    data = fetch(url)
                    ok, why = looks_ok(data, expect_pdf)
                    if ok:
                        rec["fetched_from"] = url
                        break
                    last_err, data = why, b""
                except Exception as e:  # noqa: BLE001
                    last_err, data = f"{type(e).__name__}: {e}", b""
            if data:
                target.write_bytes(data)
                rec.update(status="fetched")
            else:
                rec.update(status="paywalled" if "paywalled" in d.get("note", "") else "pending",
                           error=last_err)
        if data:
            rec.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        rec["checked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        status[d["id"]] = rec
        print(f"{rec['status']:9s} {d['id']:38s} {rec.get('error', '')}")
    (KB / "fetch_status.json").write_text(json.dumps(status, indent=2))
    n_ok = sum(1 for r in status.values() if r["status"] == "fetched")
    print(f"\n{n_ok}/{len(status)} documents fetched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
