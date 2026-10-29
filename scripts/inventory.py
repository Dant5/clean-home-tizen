"""Parse owner-collected, read-only Samsung inventories. No network or device actions."""
import argparse
import json
from pathlib import Path
import re

APP_ID = 'D5Q60BHome.CleanHome'
PACKAGE_ID = 'D5Q60BHome'
FIELD = re.compile(r'-{3,}([\w():,]+?)\s*=(.*?)-{5,}\s*$', re.M)


def consumer_records(text):
    result, fields = [], {}
    for key, value in FIELD.findall(text):
        if key == 'app_id' and fields:
            result.append(fields)
            fields = {}
        fields[key] = value.strip()
    if fields:
        result.append(fields)
    return [{
        'app_id': a.get('app_tizen_id', a.get('app_id')),
        'package_id': a.get('app_package_name'),
        'store_id': a.get('app_id'),
        'name': a.get('app_title'),
        'version': a.get('app_version'),
        'metadata': a,
    } for a in result]


def registry_records(text):
    result = []
    for line in text.splitlines():
        match = re.match(r"\s*'([^']*)'\s+'([^']+)'", line)
        if match:
            result.append({'name': match[1], 'app_id': match[2], 'package_id': None, 'version': None})
    return result


def assess(consumer_text, registry_text):
    detailed = consumer_records(consumer_text)
    registry = registry_records(registry_text)
    if not detailed or not registry:
        raise ValueError('Both detailed consumer and complete returned application-registry inventories are required.')
    by_id = {a['app_id']: a for a in registry}
    for app in detailed:
        by_id[app['app_id']] = app
    collisions = [a for a in by_id.values() if a['app_id'] == APP_ID or a.get('package_id') == PACKAGE_ID or a['app_id'].startswith(PACKAGE_ID + '.')]
    return {'applications': list(by_id.values()), 'detailed_consumer_count': len(detailed),
            'returned_registry_count': len(registry), 'identity': {'app_id': APP_ID, 'package_id': PACKAGE_ID},
            'collisions': collisions, 'no_collision_in_returned_inventory': not collisions,
            'system_package_metadata_complete': all(a.get('package_id') for a in by_id.values()),
            'coverage_note': 'Actual consumer package IDs plus all returned app IDs/prefixes checked. Protected-package IDs/versions not returned by SDB stay null; no package-ID derivation is presented as a verified value.',
            'private_tv_app_data_backed_up': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer', type=Path, required=True)
    parser.add_argument('--registry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = assess(args.consumer.read_text(), args.registry.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    args.output.chmod(0o600)
    print('Inventory saved: %d registry applications, %d detailed consumer apps, %d identity collisions.' % (result['returned_registry_count'], result['detailed_consumer_count'], len(result['collisions'])))


if __name__ == '__main__':
    main()
