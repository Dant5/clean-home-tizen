import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('startup_probe',Path(__file__).parents[1]/'scripts/startup-app-probe.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Reserved documentation address; every probe is mocked and sends no TV request.
CONFIG={'host':'192.0.2.50','protected_app_ids':['one.App','two.App']}

def test_existing_home_skips_other_probes():
    calls=[]
    def read(host,app):calls.append(app);return True
    assert m.assess(CONFIG,read)['home_visible']
    assert calls==[m.HOME_ID]

@pytest.mark.parametrize('home,protected,safe',[(False,False,True),(False,True,False),(False,None,False),(None,False,False)])
def test_fail_closed(home,protected,safe):
    result=m.assess(CONFIG,lambda host,app:home if app==m.HOME_ID else protected)
    assert result['safe_to_launch'] is safe

@pytest.mark.parametrize('override',[{'host':'8.8.8.8'},{'host':'0.0.0.0'},{'protected_app_ids':[]},{'protected_app_ids':['x; echo bad']},{'protected_app_ids':[m.HOME_ID]},{'protected_app_ids':['x']*33}])
def test_configuration_rejected_before_network(override):
    with pytest.raises(ValueError):m.assess(dict(CONFIG,**override),lambda *args:pytest.fail('Network called'))

def test_duplicate_ids_checked_once():
    calls=[]
    def read(host,app):calls.append(app);return False
    m.assess(dict(CONFIG,protected_app_ids=['same','same']),read)
    assert calls==[m.HOME_ID,'same']


@pytest.mark.parametrize('home,protected,safe', [(False, False, True), (False, True, False), (False, None, False), (None, False, False), (True, None, False)])
def test_parallel_fail_closed(home, protected, safe):
    result = m.assess(dict(CONFIG, parallel_home_check=True), lambda host, app: home if app == m.HOME_ID else protected)
    assert result['safe_to_launch'] is safe
    assert result['home_visible'] is (home is True)
    assert result['checked_apps'] == 2
    assert result['visible_app_ids'] == (CONFIG['protected_app_ids'] if protected is True else [])


@pytest.mark.parametrize('parallel', [False, True])
def test_visible_ids_distinguish_foreground_app_changes(parallel):
    result = m.assess(dict(CONFIG, parallel_home_check=parallel),
                      lambda host, app: app == 'two.App')
    assert result['visible_app_ids'] == ['two.App']
    assert result['protected_visible'] and not result['unknown_status']
    assert not result['safe_to_launch']


@pytest.mark.parametrize('value', ['false', 'true', 1, None])
def test_parallel_option_rejected_before_network(value):
    with pytest.raises(ValueError):
        m.assess(dict(CONFIG, parallel_home_check=value), lambda *args: pytest.fail('Network called'))


def test_parallel_home_read_overlaps_protected_read():
    from threading import Event
    protected_started = Event()
    def read(host, app):
        if app == m.HOME_ID:
            assert protected_started.wait(2), 'Own read serialises the consumer reads'
        else:
            protected_started.set()
        return False
    result = m.assess(dict(CONFIG, parallel_home_check=True), read)
    assert result['safe_to_launch']


def test_parallel_global_concurrency_bound_and_deduplication():
    from threading import Event, Lock
    lock, gate = Lock(), Event()
    calls, active, maximum = [], 0, 0
    def read(host, app):
        nonlocal active, maximum
        with lock:
            calls.append(app); active += 1; maximum = max(maximum, active)
            if active == 8: gate.set()
        try:
            assert gate.wait(2), 'Expected concurrent read budget was not reached'
            return False
        finally:
            with lock: active -= 1
    ids = ['test.App' + str(i) for i in range(15)]
    result = m.assess(dict(CONFIG, protected_app_ids=ids + ids, parallel_home_check=True), read)
    assert result['safe_to_launch'] and result['checked_apps'] == 15
    assert maximum == 8 and active == 0
    assert sorted(calls) == sorted([m.HOME_ID] + ids)
