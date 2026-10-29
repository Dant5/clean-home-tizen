"""Prevent accidental owner data in future source and device-profile exports."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from privacy_rules import content_findings


def test_home_network_and_hardware_addresses_are_rejected_without_echoing_values():
    private = '.'.join(map(str, [10, 25, 30, 40]))
    mac = bytes(range(6)).hex(':')
    findings = content_findings('app/device-config.js', private + ' ' + mac)
    assert set(findings) == {'literal network address', 'hardware address'}
    assert private not in str(findings) and mac not in str(findings)


def test_documentation_ips_are_test_only_and_never_a_release_device_profile():
    assert not content_findings('tests/fixture.py', '192.0.2.50')
    assert content_findings('app/device-config.js', '192.0.2.50', device_config=True)
    assert content_findings('tests/fixture.py', '.'.join(map(str, [10, 25, 30, 40])))


def test_loopback_preview_and_generic_tizen_sdk_paths_are_not_personal_data():
    assert not content_findings('scripts/preview.py', '127.0.0.1 /home/assets/icons/')
    assert not content_findings('tools/native.cs', '/home/owner/share/tmp/sdk_tools/')
    assert content_findings('app/device-config.js', '127.0.0.1', device_config=True)


def test_local_home_paths_and_assigned_identifiers_are_rejected():
    home = '/home/' + 'sample-person' + '/signing/'
    assert content_findings('scripts/example.py', home) == ['personal filesystem path']
    value = 'example' + '-device-value'
    assert content_findings('app/config.json', '{"duid":"' + value + '"}') == ['assigned device identifier or token']
    assert not content_findings('docs/template.json', '{"duid":"YOUR_DUID"}')


def test_private_material_headers_and_account_diagnostics_are_not_exports():
    header = '-----BEGIN ' + 'PRIVATE KEY-----'
    assert content_findings('app/config.js', header) == ['certificate or private-key material']
    text = 'An account ' + 'payment/spending-limit restriction'
    assert content_findings('docs/results.md', text) == ['private account diagnostic']


def test_versions_and_vector_coordinates_are_not_addresses():
    assert not content_findings('app/icon.svg', '85.0.4182.0 20.123.456.0')


def test_ipv6_hosts_are_checked_without_confusing_css_pseudo_elements():
    host = ':'.join(['fd00', 'abcd', '', '1234'])
    assert content_findings('app/device-config.js', host) == ['literal network address']
    assert not content_findings('tests/fixture.py', '2001:db8::7')
    assert not content_findings('app/style.css', '.tile::before .tile::after')
