"""Download validation protects the frozen inputs without requiring network tests."""
import hashlib
import io
import json
from urllib.error import HTTPError

import pytest

from src import download_sources
from src.download_sources import SourceDownloadError, download_manifest

PDF = b"%PDF-1.7\nAudited example bytes\n%%EOF\n"


@pytest.fixture
def source(tmp_path):
    record = {
        "season": "2025-26",
        "source_url": "https://example.org/standings.pdf",
        "file": "data/raw/2025-26.pdf",
        "sha256": hashlib.sha256(PDF).hexdigest(),
        "retrieved_at": "2026-09-30T00:00:00+00:00",
    }
    manifest = tmp_path / "sources.json"
    manifest.write_text(json.dumps([record]))
    return tmp_path, manifest, record


def fake_response(monkeypatch, data):
    calls = []

    def open_response(request, timeout):
        calls.append((request.full_url, timeout))
        return io.BytesIO(data)

    monkeypatch.setattr(download_sources, "urlopen", open_response)
    return calls


def test_download_creates_directories_and_preserves_manifest(source, monkeypatch):
    root, manifest, record = source
    before = manifest.read_bytes()
    calls = fake_response(monkeypatch, PDF)
    assert download_manifest(manifest, root=root) == (1, 0)
    assert (root / record["file"]).read_bytes() == PDF
    assert manifest.read_bytes() == before
    assert calls == [(record["source_url"], 60)]
    assert not list((root / "data/raw").glob("*.part"))


def test_verified_cache_does_not_request_network(source, monkeypatch):
    root, manifest, record = source
    target = root / record["file"]
    target.parent.mkdir(parents=True)
    target.write_bytes(PDF)
    calls = fake_response(monkeypatch, b"unexpected network response")
    assert download_manifest(manifest, root=root) == (0, 1)
    assert calls == []


def test_invalid_cache_is_replaced_only_with_verified_bytes(source, monkeypatch):
    root, manifest, record = source
    target = root / record["file"]
    target.parent.mkdir(parents=True)
    target.write_bytes(b"truncated")
    fake_response(monkeypatch, PDF)
    assert download_manifest(manifest, root=root) == (1, 0)
    assert target.read_bytes() == PDF


@pytest.mark.parametrize("response,message", [
    (b"<html>error</html>", "response is not a PDF"),
    (b"%PDF-1.7 changed source", "SHA-256 mismatch"),
])
def test_bad_download_does_not_save_partial_pdf(source, monkeypatch, response, message):
    root, manifest, record = source
    fake_response(monkeypatch, response)
    with pytest.raises(SourceDownloadError, match=message):
        download_manifest(manifest, root=root)
    assert not (root / record["file"]).exists()


def test_failed_force_refresh_preserves_valid_cached_file(source, monkeypatch):
    root, manifest, record = source
    target = root / record["file"]
    target.parent.mkdir(parents=True)
    target.write_bytes(PDF)
    fake_response(monkeypatch, b"%PDF-1.7 different bytes")
    with pytest.raises(SourceDownloadError, match="SHA-256 mismatch"):
        download_manifest(manifest, root=root, force=True)
    assert target.read_bytes() == PDF


def test_http_error_explains_manual_recovery(source, monkeypatch):
    root, manifest, record = source

    def fail(request, timeout):
        raise HTTPError(request.full_url, 503, "unavailable", {}, None)

    monkeypatch.setattr(download_sources, "urlopen", fail)
    with pytest.raises(SourceDownloadError, match=r"HTTP 503.*docs/DATA_DOWNLOADS.md"):
        download_manifest(manifest, root=root)
    assert not (root / record["file"]).exists()


def test_manifest_cannot_write_outside_raw_directory(source, monkeypatch):
    root, manifest, record = source
    record["file"] = "../outside.pdf"
    manifest.write_text(json.dumps([record]))
    calls = fake_response(monkeypatch, PDF)
    with pytest.raises(SourceDownloadError, match="inside data/raw"):
        download_manifest(manifest, root=root)
    assert calls == []
