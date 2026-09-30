#!/usr/bin/env bash
# Rebuild the research and run tests; --offline uses committed audited tables.
set -euo pipefail
cd "$(dirname "$0")"
python_bin="${PYTHON:-python3}"
if [[ -z "${PYTHON:-}" && -x .venv/bin/python ]]; then
  python_bin=".venv/bin/python"
fi
mode="${1:-}"
if [[ $# -gt 1 || ( -n "$mode" && "$mode" != "--download" && "$mode" != "--offline" ) ]]; then
  echo "Usage: ./run.sh [--download | --offline]" >&2
  echo "Default: fetch audited PDFs; --download: refresh; --offline: rebuild from committed CSVs." >&2
  exit 2
fi
if [[ "$mode" != "--offline" ]]; then
  # Bash 3.2 treats an empty array expansion as unbound under set -u.
  if [[ "$mode" == "--download" ]]; then
    "$python_bin" src/fetch_sources.py --force
    "$python_bin" src/fetch_seasonal.py --force
  else
    "$python_bin" src/fetch_sources.py
    "$python_bin" src/fetch_seasonal.py
  fi
  "$python_bin" src/parse_standings.py
  "$python_bin" src/parse_seasonal.py
fi
"$python_bin" src/combine_sports.py
"$python_bin" src/build_database.py
"$python_bin" -m src.analyze
"$python_bin" -m src.export_tableau
"$python_bin" -m src.ml_benchmark
"$python_bin" -m pytest -q
