"""Publication regressions: scan real tracked content, not an exclusion baseline."""
from pathlib import Path
import subprocess
from urllib.parse import quote

import pytest
from scripts.check_public_urls import tokenized_urls, tracked_findings

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('key', [
    'X-Amz-Credential', 'X-Amz-Security-Token', 'X-Amz-Signature', 'Signature',
    'Security-Token', 'session_id', 'ticketID', 'PHPSESSID', 'hkey', 'access_token',
])
def test_signed_and_session_parameters_are_rejected(key):
    # Construct synthetic examples at runtime; no credential URL is stored in Git.
    url = 'https://' + 'example.org/source?' + key + '=synthetic'
    assert tokenized_urls(url)
    assert tokenized_urls(quote(quote(url, safe=''), safe=''))
    assert tokenized_urls(url.replace('?', '?id=12&amp;'))


def test_canonical_wayback_and_document_id_are_allowed():
    assert not tokenized_urls('https://web.archive.org/web/20251001093455/https://smumustangs.com/')
    assert not tokenized_urls('https://nacda.com/documents/2018/7/18/June29overallDI.pdf?id=1799')


def test_all_tracked_files_have_no_tokenized_urls():
    assert not tracked_findings(ROOT), 'Remove tokenized URLs; never publish their values.'


def test_index_check_detects_staged_url_even_when_worktree_is_clean(tmp_path):
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    path = tmp_path / 'evidence.csv'
    path.write_text('https://' + 'example.org/source?' + 'Signature' + '=synthetic\n')
    subprocess.run(['git', 'add', 'evidence.csv'], cwd=tmp_path, check=True)
    path.write_text('https://example.org/source\n')
    assert not tracked_findings(tmp_path)
    assert tracked_findings(tmp_path, staged=True) == [('evidence.csv', 1, 'Signature')]


def test_private_inputs_and_local_state_are_not_tracked():
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in filter(None, names):
        assert not name.startswith('data/raw/')
        assert 'search_log' not in name and 'retrieval_log' not in name
        assert '.duckdb' not in name
        assert Path(name).name == '.env.example' or not Path(name).name.startswith('.env')


def test_json_unicode_and_mixed_encoding_cannot_hide_parameters():
    base = 'https://' + 'example.org/source?'
    url = base + 'Signature' + '=synthetic'
    variants = [
        url.replace('Signature', chr(92) + 'u0053ignature'),
        url.replace('=', chr(92) + 'u003d'),
        url.replace('?', chr(92) + 'u003F'),
        url.replace('://', ''.join(chr(92) + f'u{ord(c):04x}' for c in '://')),
    ]
    for variant in variants:
        assert tokenized_urls(variant)
        assert tokenized_urls(quote(variant, safe=''))
