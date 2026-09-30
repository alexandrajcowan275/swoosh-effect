# Publication checks

This repository starts with a single clean initial commit. Private working history,
raw third-party webpages, search/retrieval logs, and downloaded source PDFs are
not included. Evidence tables preserve canonical source URLs, Wayback snapshot
URLs, dates, source types, and explicit inference flags. Downloaded PDFs are local
cache files checked against the frozen source manifests.

No secrets are needed to run the project. Do not add credentials or signed URLs
to evidence tables, reports, notebooks, fixtures, or documentation. Keep `.env`
files local; `.env.example` contains comments only. Ordinary public document IDs
in URLs are retained because they identify sources rather than sessions.

After installing requirements, enable the pinned Gitleaks and URL hooks:

```bash
.venv/bin/pre-commit install
.venv/bin/python scripts/check_public_urls.py
```

The first hook run downloads Gitleaks v8.30.1 and its Go build environment through
pre-commit. Internet access is required for that first setup. The Gitleaks hook
scans staged changes with redacted output. The URL hook inspects the entire Git
index, including partially staged files. The pytest security check examines the
working copies of all tracked files, including reports, CSVs and notebooks.
No known findings are suppressed with an allowlist.

For a release, scan the complete Git history as well (install the same Gitleaks
version from its [official release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)):

```bash
gitleaks git . --log-opts="--all --full-history" --redact=100 --ignore-gitleaks-allow
.venv/bin/python scripts/check_public_urls.py --staged
```

The URL checker handles HTML entities, JSON URL escapes and percent encoding.
It rejects signature, credential, security-token, session/ticket and common API
token parameters, including all AWS/Google signed-URL parameter prefixes. It
reports file names, line numbers and parameter names without exposing values.
Secret scanners reduce risk; a passing scan does not establish that every
possible secret format can be detected.
