"""Fresh-checkout tests never download raw sources or depend on test ordering."""
from pathlib import Path
import socket
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Tests use committed fixtures or mocked responses, never live services."""
    def blocked(*args, **kwargs):
        raise AssertionError('Network access is forbidden in the test suite')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    monkeypatch.setattr(socket, 'create_connection', blocked)


@pytest.fixture(scope='session', autouse=True)
def prepared_database():
    """Build the ignored database from committed, audited CSVs before any test."""
    from src.build_database import build
    build()
