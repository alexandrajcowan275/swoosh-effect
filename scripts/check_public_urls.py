"""Reject credential-bearing URLs without printing their values.

Default: inspect working copies of all tracked files (used by pytest/CI).
--staged: inspect the entire Git index (used by pre-commit, including partial stages).
Only the standard library is needed. Source IDs such as NACDA's ?id=1799 are safe.
"""
from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

URL = re.compile(r'https?://[^\s<>"\'\\]+', re.IGNORECASE)
PARAMETER = re.compile(r'[?&;#]([^=?&;#]+)=')
BLOCKED_KEYS = {
    'signature', 'sig', 'securitytoken', 'token', 'accesstoken', 'refreshtoken',
    'idtoken', 'authtoken', 'authorization', 'auth', 'authkey', 'apikey',
    'accesskey', 'awsaccesskeyid', 'credential', 'credentials', 'secret',
    'password', 'session', 'sessionid', 'sid', 'phpsessid', 'jsessionid',
    'ticket', 'ticketid', 'hkey', 'captcha', 'captchakey', 'policy', 'keypairid',
}


def decoded(text: str) -> str:
    """Handle HTML, JSON slash/ampersand escapes and percent-encoded parameters."""
    for _ in range(8):
        expanded = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        expanded = expanded.replace(r'\/', '/')
        result = html.unescape(unquote(expanded))
        if result == text:
            break
        text = result
    return text


def forbidden_key(key: str) -> bool:
    normalized = re.sub(r'[^a-z0-9]', '', decoded(key).lower())
    return (normalized in BLOCKED_KEYS or normalized.startswith(('xamz', 'xgoog'))
            or normalized.startswith(('session', 'ticket'))
            or normalized.endswith(('token', 'signature')))


def tokenized_urls(text: str) -> list[tuple[int, str]]:
    """Return line numbers and parameter names only; never return URL values."""
    expanded = decoded(text)
    findings = []
    for match in URL.finditer(expanded):
        for parameter in PARAMETER.finditer(match.group()):
            if forbidden_key(parameter.group(1)):
                line = expanded.count('\n', 0, match.start()) + 1
                findings.append((line, parameter.group(1)))
    return findings


def tracked_findings(root: Path, *, staged: bool = False) -> list[tuple[str, int, str]]:
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    findings = []
    for name in filter(None, files):
        if staged:
            content = subprocess.check_output(['git', 'show', f':{name}'], cwd=root)
        else:
            path = root / name
            if not path.is_file():
                continue
            content = path.read_bytes()
        # Decode binary containers too, so an embedded plaintext URL is checked.
        for line, key in tokenized_urls(content.decode('utf-8', errors='ignore')):
            findings.append((name, line, key))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    findings = tracked_findings(root, staged=args.staged)
    for name, line, key in findings:
        print(f'{name}:{line}: forbidden URL parameter {key!r} (value redacted)')
    print(f'Tokenized URL findings: {len(findings)}')
    return int(bool(findings))


if __name__ == '__main__':
    raise SystemExit(main())
