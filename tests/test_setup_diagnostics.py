"""Unsupported TVs must yield useful sanitized reports without Home writes."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import threading
import urllib.request
import urllib.error
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/home-setup'))
import diagnostics as diag
import reports
from vendor.aerotizen.sdb import SdbError
spec=importlib.util.spec_from_file_location('diagnostic_wizard',ROOT/'tools/home-setup/setup.py')
wizard=importlib.util.module_from_spec(spec);spec.loader.exec_module(wizard)


def native():
    report=reports.new_report()
    checks={name:['pass','OK','Other'] for name in diag.NATIVE}
    checks['identity']=['pass','OK','SDK'];checks['architecture']=['pass','OK','None']
    return {'readOnly':True,'architecture':'ARM64','firmware':'T-EXAMPLE-1000.0','checks':checks}


class Session:
    deadline=None
    def __init__(self,fail=False): self.fail=fail;self.closed=False
    def connect(self,attempts):
        assert attempts==1
        if self.fail: raise SdbError('PRIVATE connection detail')
    def capability(self): return {'platform_version':'.'.join(map(str,[9,0,0,1])),'serial':'PRIVATE'}  # Four-part Samsung OS version, not an IP address.
    def close(self): self.closed=True


def runner(monkeypatch,data=None,meta=None,fail=False):
    monkeypatch.setattr(diag,'private_ipv4',lambda x:'TV_FIXTURE')
    session=Session(fail);calls=[]
    def run(connection,files,entry,args,*,diagnostic):
        calls.append(1)
        assert diagnostic and entry=='CleanHomeReadOnlyInspection.dll' and args==('--compatibility',)
        assert all('ReadOnlyInspection' in name for name in files)
        return {'stdout':json.dumps(data if data is not None else native()),'exit_code':0,'staging_cleaned':True}
    read=lambda h: meta if meta is not None else {'modelName':'QNTESTTV','type':'Samsung SmartTV','serial':'PRIVATE','networkAddress':'PRIVATE'}
    return diag.Diagnostics({'CleanHomeReadOnlyInspection.dll':b'fixture','CleanHomeNativeControl.dll':b'NEVER STAGE'},get_metadata=read,session_factory=lambda h:session,native_run=run),session,calls


def test_new_model_reaches_all_getters_without_home_changes(monkeypatch):
    check,session,calls=runner(monkeypatch)
    result=check.run('TV_FIXTURE')
    assert result['profile']=='needs-review' and result['architecture']=='ARM64'
    assert result['tizen']=='9.0.0' and result['checks']['lastApp'][0]=='pass'
    assert result['checks']['homeSetup']==['skipped','PROFILE_NEEDED','None']
    assert len(calls)==1 and session.closed and 'PRIVATE' not in json.dumps(result)


def test_independent_getter_failures_do_not_hide_later_results(monkeypatch):
    data=native();data['checks']['homeOperation']=['unavailable','MISSING_SYMBOL','None']
    check,_,_=runner(monkeypatch,data=data)
    result=check.run('TV_FIXTURE')
    assert result['checks']['homeOperation'][1]=='MISSING_SYMBOL'
    assert result['checks']['lastApp'][0]=='pass'


def test_failed_developer_connection_still_has_metadata_report(monkeypatch):
    check,session,calls=runner(monkeypatch,fail=True)
    result=check.run('TV_FIXTURE')
    assert result['model']=='QNTESTTV' and result['checks']['developer'][1]=='SDB_FAILED'
    assert not calls and session.closed and 'PRIVATE' not in json.dumps(result)


def test_unidentified_device_never_stages_native_helper(monkeypatch):
    check,_,calls=runner(monkeypatch,meta={'modelName':'EXAMPLE_DEVICE'})
    result=check.run('TV_FIXTURE')
    assert result['checks']['developer'][0]=='pass' and result['checks']['nativeHelper'][1]=='NOT_SAMSUNG'
    assert not calls


@pytest.mark.parametrize('fault',['extra','privateValue','badArchitecture','notReadOnly'])
def test_malformed_native_output_is_dropped(monkeypatch,fault):
    data=native()
    if fault=='extra': data['address']='PRIVATE'
    elif fault=='privateValue': data['checks']['lastApp'][2]='PRIVATE'
    elif fault=='badArchitecture': data['architecture']='PRIVATE'
    else: data['readOnly']=False
    check,_,_=runner(monkeypatch,data=data)
    result=check.run('TV_FIXTURE')
    assert result['checks']['nativeHelper'][1]=='INVALID_RESULT'
    assert 'PRIVATE' not in json.dumps(result)


@pytest.mark.parametrize('key',['address','serial','apps','originalHome','logs'])
def test_report_rejects_extra_fields(key):
    value=reports.new_report();value[key]='PRIVATE'
    with pytest.raises(ValueError): reports.validate(value)


def test_report_rejects_arbitrary_messages_and_fits_receiver_limit():
    value=reports.new_report();value['checks']['lastApp']=['fail','PRIVATE','None']
    with pytest.raises(ValueError): reports.validate(value)
    value=reports.new_report();value['model']='Q'+'A'*39;value['firmware']='T-X'+'A'*60
    for name in value['checks']:value['checks'][name]=['unavailable','STRICT_CHECK_FAILED','Unavailable']
    assert len(json.dumps(reports.validate(value),separators=(',',':')).encode())<=2048


def test_diagnostic_sdk_execution_cannot_stage_write_helper():
    from vendor.aerotizen.sdk import build_script
    with pytest.raises(ValueError,match='getter-only'):
        build_script({'CleanHomeNativeControl.dll':b'fixture'},'CleanHomeNativeControl.dll',('apply-all',),'127.0.0.1',1234,'a'*12,diagnostic=True)
    files={'CleanHomeReadOnlyInspection'+suffix:b'fixture' for suffix in ('.dll','.runtimeconfig.json','.deps.json')}
    script,_,_,_=build_script(files,'CleanHomeReadOnlyInspection.dll',('--compatibility',),'127.0.0.1',1234,'a'*12,diagnostic=True)
    assert 'CLEAN_HOME_ROOT_REFUSED' in script and ' = 901' not in script


def test_unknown_tv_report_send_is_explicit_private_and_deduplicated():
    report=reports.new_report();report['model']='QNTESTTV';report['profile']='needs-review'
    class FakeDiagnostics:
        def run(self,host): return copy.deepcopy(report)
    class NoWrites:
        def perform(self,*args): raise AssertionError('Unsupported diagnostics must not inspect originals or write Home')
    sent=[]
    def sender(value): sent.append(value);return 'CH-00000000-0000-0000-0000-000000000000'
    server=wizard.create_server(NoWrites(),FakeDiagnostics(),sender)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url='http://127.0.0.1:'+str(server.server_port)
    try:
        import re
        html=urllib.request.urlopen(url).read().decode();token=re.search(r'nonce="([a-f0-9]+)"',html)[1]
        def post(action,confirmed=False,host='TV_FIXTURE'):
            req=urllib.request.Request(url+'/action',data=json.dumps({'host':host,'action':action,'confirmed':confirmed}).encode(),headers={'Content-Type':'application/json','X-Clean-Home':token})
            return json.load(urllib.request.urlopen(req))
        result=post('diagnose');assert not result['canApply'] and result['report']['profile']=='needs-review' and not sent
        with pytest.raises(urllib.error.HTTPError):urllib.request.urlopen(url+'/report/wrong.json')
        saved=urllib.request.urlopen(url+'/report/'+token+'.json')
        assert 'attachment' in saved.headers['Content-Disposition'] and json.load(saved)==report
        with pytest.raises(urllib.error.HTTPError):post('send-report')
        assert post('send-report',True)['receipt'].startswith('CH-')
        assert post('send-report',True)['duplicate'] and len(sent)==1
        with pytest.raises(urllib.error.HTTPError):post('send-report',True,'DIFFERENT_TV')
        assert 'TV_FIXTURE' not in json.dumps(sent)
    finally:server.shutdown();server.server_close();thread.join(2)


@pytest.mark.parametrize('status,payload,accepted',[
    (201,{'accepted':True,'id':'CH-00000000-0000-0000-0000-000000000000'},True),
    (200,{'accepted':True,'id':'CH-00000000-0000-0000-0000-000000000000'},False),
    (201,{'accepted':False,'id':'CH-00000000-0000-0000-0000-000000000000'},False),
    (201,{'accepted':True,'id':'PRIVATE'},False),
    (201,{'accepted':True,'id':'X'*300},False),
])
def test_sender_requires_bounded_confirmed_receipt(monkeypatch,status,payload,accepted):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,size):return json.dumps(payload).encode()[:size]
    response=Response();response.status=status
    class Opener:
        def open(self,request,timeout):
            assert request.full_url==reports.ENDPOINT and timeout==10
            assert request.get_header('User-agent')=='CleanHome-Setup/'+reports.VERSION
            assert reports.validate(json.loads(request.data))
            assert 'PRIVATE' not in request.data.decode()
            return response
    monkeypatch.setattr(reports.urllib.request,'build_opener',lambda *args:Opener())
    if accepted:assert reports.send(reports.new_report()).startswith('CH-')
    else:
        with pytest.raises(ValueError) as caught:reports.send(reports.new_report())
        assert 'PRIVATE' not in str(caught.value)


@pytest.mark.parametrize('failure',[False,True])
def test_supported_setup_outcome_is_in_report_without_native_error_text(failure):
    report=reports.new_report();report['profile']='known'
    class KnownDiagnostics:
        def run(self,host):return copy.deepcopy(report)
    class Companion:
        def perform(self,host,action):
            if action=='inspect':return {'phase':'original','canApply':True,'canUndo':True,'active':False,'recovery':'PRIVATE_LOCAL_FOLDER'}
            if failure:raise SdbError('PRIVATE_NATIVE_ERROR')
            return {'success':True,'message':'Verified'}
    server=wizard.create_server(Companion(),KnownDiagnostics())
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
    try:
        import re
        token=re.search(r'nonce="([a-f0-9]+)"',urllib.request.urlopen(url).read().decode())[1]
        def post(action):
            request=urllib.request.Request(url+'/action',data=json.dumps({'host':'TV_FIXTURE','action':action,'confirmed':True}).encode(),headers={'Content-Type':'application/json','X-Clean-Home':token})
            try:return json.load(urllib.request.urlopen(request))
            except urllib.error.HTTPError as error:return json.load(error)
        assert post('diagnose')['canApply']
        result=post('apply');saved=result['report']
        assert saved['action']=='apply' and saved['phase']==('unknown' if failure else 'active')
        assert saved['checks']['homeSetup'][1]==('NOT_CONFIRMED' if failure else 'OK')
        assert 'PRIVATE' not in json.dumps(saved) and 'PRIVATE_NATIVE_ERROR' not in json.dumps(result)
    finally:server.shutdown();server.server_close();thread.join(2)
