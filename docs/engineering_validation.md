# Engineering validation

## CI — 2026-09-30

Commit `30f6e66` passed [GitHub Actions run 36746018965](https://github.com/alexandrajcowan275/swoosh-effect/actions/runs/36746018965).
Python 3.12.14 on Ubuntu 24.04 ran all 98 tests, pre-commit secret and URL checks,
and the complete Git-history Gitleaks scan. No research PDFs were downloaded.

## Docker — 2026-09-30

Built `swoosh-effect` locally on Apple Silicon using Docker CLI 29.8.1 and
Colima 0.10.3 (profile `swoosh`). The base is Python 3.12.14 slim Bookworm,
pinned by the multi-platform manifest digest in `Dockerfile`.

`docker --context colima-swoosh run --rm --network none swoosh-effect`
completed the offline pipeline and all **98 tests passed in 7.84 seconds**.
An independent `id -u` invocation returned **10001**. The run had no network,
no mounted host files, and no downloaded source PDFs. The application outputs
remain inside the disposable container; host research outputs are unchanged.
