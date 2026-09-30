# Offline test fixtures

`synthetic_final.pdf` and `synthetic_fall.pdf` are original, tiny test documents,
not extracts or copies of third-party source pages. They exercise PDF text and
coordinate extraction, institution/conference boundaries, explicit zero,
excluded `x`, sport headers, subtotals, and checksum validation. All schools and
scores in these two documents are fictional. Regenerate both deterministically
with `python scripts/make_test_pdfs.py`; `pdf_manifest.json` records their hashes.

The existing top-five transcription and Phase 3 regression fixtures preserve
checks against the audited, committed research tables. The full pytest suite
runs without `data/raw/` or network access. Full raw-document checksum validation
still runs in `run.sh` during download and parsing; it is deliberately outside CI.
