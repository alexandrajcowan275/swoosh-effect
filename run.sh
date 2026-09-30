#!/usr/bin/env bash
# Download missing audited PDFs, then rebuild every analysis output and run tests.
set -euo pipefail
cd "$(dirname "$0")"
python_bin="${PYTHON:-python3}"
if [[ -z "${PYTHON:-}" && -x .venv/bin/python ]]; then
  python_bin=".venv/bin/python"
fi
if [[ "${1:-}" == "--download" && $# == 1 ]]; then
  set -- --force
elif [[ $# != 0 ]]; then
  echo "Usage: ./run.sh [--download]" >&2
  echo "By default, download missing/invalid PDFs; --download refreshes every PDF." >&2
  exit 2
fi
"$python_bin" src/fetch_sources.py "$@"
"$python_bin" src/fetch_seasonal.py "$@"
"$python_bin" src/parse_standings.py
"$python_bin" src/parse_seasonal.py
"$python_bin" src/combine_sports.py
"$python_bin" src/build_database.py
"$python_bin" -m src.analyze
"$python_bin" -m src.export_tableau
"$python_bin" -m pytest -q
