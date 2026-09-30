"""Verify portable shell routing without downloads or model execution."""
from pathlib import Path
import os
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("mode", ["", "--download", "--offline"])
def test_run_sh_routes_modes(tmp_path, mode):
    script = tmp_path / "run.sh"
    script.write_bytes((ROOT / "run.sh").read_bytes())
    runner = tmp_path / "python-stub"
    runner.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALL_LOG"\n')
    runner.chmod(0o755)
    log = tmp_path / "calls.txt"
    env = dict(os.environ, PYTHON=str(runner), CALL_LOG=str(log))
    command = ["/bin/bash", str(script)] + ([mode] if mode else [])
    subprocess.run(command, env=env, check=True, capture_output=True, text=True)
    calls = log.read_text().splitlines()
    if mode == "--offline":
        assert not any("fetch_" in call or "parse_" in call for call in calls)
    else:
        suffix = " --force" if mode == "--download" else ""
        assert calls[:2] == ["src/fetch_sources.py" + suffix, "src/fetch_seasonal.py" + suffix]
    assert calls[-2:] == ["-m src.ml_benchmark", "-m pytest -q"]
