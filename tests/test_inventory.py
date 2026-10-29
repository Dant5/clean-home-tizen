import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('inventory', Path(__file__).resolve().parents[1] / 'scripts/inventory.py')
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


def consumer(app='Legacy.App', package='Legacy.Native', version='2.0.4'):
    return '\n'.join('  --------------%s =%s-------------' % pair for pair in [('app_id', app), ('app_tizen_id', app), ('app_package_name', package), ('app_title', 'Legacy'), ('app_version', version)])


def test_indented_cli_output_preserves_multiple_records_and_real_native_package_id():
    parsed = inventory.consumer_records(consumer() + '\n' + consumer('Moon.Stream', 'Moon', '1.17.2'))
    assert len(parsed) == 2
    assert parsed[0]['package_id'] == 'Legacy.Native'
    assert parsed[1]['version'] == '1.17.2'


def test_collision_found_even_if_only_present_in_system_registry():
    result = inventory.assess(consumer(), "\t'Existing'\t'D5Q60BHome.Other'\n")
    assert result['collisions']
    assert not result['no_collision_in_returned_inventory']


def test_package_collision_found_when_native_application_id_has_different_prefix():
    result = inventory.assess(consumer('Native.Different', 'D5Q60BHome'), " 'Native' 'Native.Different'\n")
    assert result['collisions']


def test_unknown_system_packages_remain_unknown_and_do_not_claim_data_backup():
    result = inventory.assess(consumer(), " 'System' 'org.tizen.system'\n")
    assert result['no_collision_in_returned_inventory']
    assert not result['system_package_metadata_complete']
    assert not result['private_tv_app_data_backed_up']
    assert next(a for a in result['applications'] if a['app_id'] == 'org.tizen.system')['package_id'] is None


def test_missing_inventory_is_not_a_successful_collision_check():
    with pytest.raises(ValueError):
        inventory.assess('', " 'System' 'org.tizen.system'\n")
