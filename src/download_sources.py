"""Download the exact, hash-verified PDFs described by a frozen source manifest."""
from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


class SourceDownloadError(RuntimeError):
    """A source could not be retrieved without changing the audited input data."""


def _verify_pdf(data: bytes, expected_hash: str) -> str | None:
    if not data.startswith(b"%PDF-"):
        return "response is not a PDF"
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != expected_hash:
        return f"SHA-256 mismatch (expected {expected_hash}, received {actual_hash})"
    return None


def download_manifest(manifest_path: Path, *, root: Path = ROOT,
                      force: bool = False) -> tuple[int, int]:
    """Fetch missing/invalid PDFs, returning (downloaded, reused) counts.

    The manifest, including its original retrieval dates, is never modified.
    Bytes must match both the PDF signature and the audited SHA-256 digest.
    Validated downloads replace files atomically, preserving a valid cached
    file if a forced refresh fails. Only paths inside ``data/raw`` are allowed.
    """
    records = json.loads(manifest_path.read_text())
    downloaded = reused = 0
    raw_root = (root / "data/raw").resolve()
    for record in records:
        path = (root / record["file"]).resolve()
        url = record["source_url"]
        expected_hash = record["sha256"]
        label = f"{record['season']} {record.get('period', 'final')}"
        if not path.is_relative_to(raw_root) or path == raw_root:
            raise SourceDownloadError(f"{label}: manifest path must be inside data/raw")
        if urlsplit(url).scheme != "https" or not urlsplit(url).netloc:
            raise SourceDownloadError(f"{label}: source URL must use HTTPS")
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            raise SourceDownloadError(f"{label}: invalid SHA-256 in source manifest")

        if not force and path.is_file():
            if _verify_pdf(path.read_bytes(), expected_hash) is None:
                reused += 1
                print(f"Using verified PDF: {record['file']}", flush=True)
                continue
            print(f"Replacing invalid cached PDF: {record['file']}", flush=True)

        request = Request(url, headers={"User-Agent": "swoosh-effect/1.0 (research reproducibility)"})
        try:
            with urlopen(request, timeout=60) as response:
                data = response.read()
        except (HTTPError, URLError, OSError) as error:
            # Do not echo server-provided redirects or potentially signed URLs.
            detail = f"HTTP {error.code}" if isinstance(error, HTTPError) else type(error).__name__
            raise SourceDownloadError(
                f"{label}: download failed ({detail}). See docs/DATA_DOWNLOADS.md; "
                f"save the listed PDF as {record['file']} and rerun."
            ) from None
        problem = _verify_pdf(data, expected_hash)
        if problem:
            raise SourceDownloadError(
                f"{label}: {problem}. No source file was replaced. "
                "See docs/DATA_DOWNLOADS.md; do not change the manifest hash to bypass validation."
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(data)
            temporary_path.replace(path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        downloaded += 1
        print(f"Downloaded and verified: {record['file']} ({len(data):,} bytes)", flush=True)
    return downloaded, reused
