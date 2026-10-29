"""Small, value-redacting privacy rules for source and unsigned release files.

These supplement Gitleaks. They do not prove that arbitrary content is private-data free.
"""
import ipaddress
from pathlib import PurePosixPath
import re

IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
IPV6 = re.compile(r'(?i)(?<![A-Za-z0-9_.:])(?:[0-9a-f]{0,4}:){2,}[0-9a-f:.]{0,39}(?![A-Za-z0-9_.:])')
MAC = re.compile(r'(?i)(?<![\w:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![\w:])')
HOST_HOME = re.compile(r"(?:/Users/[A-Za-z0-9_.@ -]+/|/home/[A-Za-z0-9_.@-]+/|[A-Za-z]:[/\\]Users[/\\][A-Za-z0-9_.@ -]+[/\\])")
MATERIAL = re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?(?:PRIVATE KEY|CERTIFICATE)-----')
TOKEN = re.compile(r'gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|AKIA[A-Z0-9]{16}')
PERSONAL_STATUS = re.compile(r'(?i)account\s+(?:payment|billing)|billing/spending[- ]limit|recent\s+account\s+payments')
ASSIGNED_ID = re.compile(r'''(?ix)["'](?:duid|serial_number|serialNumber|access_token|refresh_token|tv_token)["']\s*[:=]\s*["']([^"']+)["']''')
DOCUMENTATION = tuple(ipaddress.ip_network(n) for n in ('192.0.2.0/24', '198.51.100.0/24', '203.0.113.0/24', '2001:db8::/32'))


def addresses(text):
    for match in list(IPV4.finditer(text)) + list(IPV6.finditer(text)):
        try:
            yield ipaddress.ip_address(match.group())
        except ValueError:
            pass  # SVG path coordinates and software versions are not IP addresses.


def content_findings(name, text, *, device_config=False):
    """Return categories only, never found credential or identifier values."""
    findings = set()
    test = PurePosixPath(name).parts[0] == 'tests' if name else False
    for address in addresses(text):
        # Local preview/fake socket tests need loopback. Reserved documentation
        # addresses and a public DNS rejection fixture are allowed only in tests.
        permitted = address.is_loopback or (test and (address.is_unspecified or any(address in n for n in DOCUMENTATION) or str(address) == '8.8.8.8'))
        if name == 'scripts/privacy_rules.py' and (any(address == n.network_address for n in DOCUMENTATION) or str(address) == '8.8.8.8'):
            permitted = True  # Reviewed constants defining safe test data.
        if device_config or not permitted:
            findings.add('literal network address')
    if MAC.search(text):
        findings.add('hardware address')
    for match in HOST_HOME.finditer(text):
        path = match.group()
        # These are the preview's URL route and Samsung's generic SDK path,
        # respectively, rather than a developer's home directory.
        if path.startswith('/home/assets/') or path == '/home/owner/':
            continue
        findings.add('personal filesystem path')
    if MATERIAL.search(text):
        findings.add('certificate or private-key material')
    if TOKEN.search(text):
        findings.add('credential pattern')
    if PERSONAL_STATUS.search(text):
        findings.add('private account diagnostic')
    placeholders = {'YOUR_DUID', 'YOUR_SERIAL', 'EXAMPLE_DUID', 'EXAMPLE_SERIAL', 'REDACTED'}
    if any(match.group(1) not in placeholders for match in ASSIGNED_ID.finditer(text)):
        findings.add('assigned device identifier or token')
    return sorted(findings)
