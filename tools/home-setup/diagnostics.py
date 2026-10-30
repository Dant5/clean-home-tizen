"""Cross-model capability probes. No Home writes, app launches or identity reads."""
import json
import re
import time
import urllib.request
from core import private_ipv4, MODEL, FIRMWARE
from reports import new_report, validate, clean_model, clean_firmware, clean_tizen
from vendor.aerotizen.transport import BoundedSdb
from vendor.aerotizen import sdk

NATIVE = ('identity','architecture','homeOperation','homePreference','startupPreference','bootingPreference','firstScreen','autoStart','lastApp','appBoot')


def metadata(host):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args): return None
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open('http://'+host+':8001/api/v2/',timeout=5) as response:
        raw=response.read(65537)
        if len(raw)>65536: raise ValueError('Metadata limit')
        return json.loads(raw).get('device',{})


class Diagnostics:
    def __init__(self,files,*,get_metadata=metadata,session_factory=BoundedSdb,native_run=sdk.run):
        self.files={k:v for k,v in files.items() if k.startswith('CleanHomeReadOnlyInspection.')}
        self.get_metadata,self.session_factory,self.native_run=get_metadata,session_factory,native_run

    def run(self,host):
        host=private_ipv4(host)
        report=new_report();checks=report['checks'];identified=False
        try:
            device=self.get_metadata(host)
            report['model']=clean_model(device.get('modelName',device.get('model')))
            report['firmware']=clean_firmware(device.get('firmwareVersion'))
            identified=device.get('type')=='Samsung SmartTV' or bool(re.fullmatch(r'(?:QA|QE|QN|UE|UA|UN|LS|HG|GU|GQ)[A-Za-z0-9_-]+',report['model']))
            checks['metadata']=['pass','OK','None'] if identified else ['fail','NOT_SAMSUNG','None']
        except Exception: checks['metadata']=['fail','HTTP_FAILED','None']
        connection=None
        try:
            try:
                connection=self.session_factory(host)
                connection.connect(attempts=1);checks['developer']=['pass','OK','None']
            except Exception:
                checks['developer']=['fail','SDB_FAILED','None'];return validate(report)
            try:
                connection.deadline=time.monotonic()+8
                caps=connection.capability()
                report['tizen']=clean_tizen(caps.get('tizen_version',caps.get('platform_version')))
                checks['capabilities']=['pass','OK','None']
            except Exception: checks['capabilities']=['unavailable','CAPS_FAILED','None']
            finally: connection.deadline=None
            if not identified:
                checks['nativeHelper']=['skipped','NOT_SAMSUNG','None'];return validate(report)
            try:
                raw=self.native_run(connection,self.files,'CleanHomeReadOnlyInspection.dll',('--compatibility',),diagnostic=True)
            except Exception:
                checks['nativeHelper']=['fail','CLEANUP_UNKNOWN','None'];return validate(report)
            if raw.get('staging_cleaned') is not True:
                checks['nativeHelper']=['fail','CLEANUP_UNKNOWN','None'];return validate(report)
            if raw.get('exit_code')!=0:
                checks['nativeHelper']=['fail','ROOT_REFUSED' if 'CLEAN_HOME_ROOT_REFUSED' in raw.get('stdout','') else 'NATIVE_TOOL_MISSING' if raw.get('exit_code')==127 else 'HELPER_FAILED','None'];return validate(report)
            try:
                lines=[line for line in raw['stdout'].splitlines() if line.startswith('{')]
                if len(lines)!=1: raise ValueError()
                data=json.loads(lines[0])
                if set(data)!= {'readOnly','architecture','firmware','checks'} or data['readOnly'] is not True or set(data['checks'])!=set(NATIVE): raise ValueError()
                report['architecture']=data['architecture']
                report['firmware']=clean_firmware(data['firmware'])
                for name in NATIVE: checks[name]=data['checks'][name]
                validate(report)
                checks['nativeHelper']=['pass','OK','None']
            except Exception:
                # Drop the whole untrusted helper response, retaining earlier safe checks.
                for name in NATIVE: checks[name]=['skipped','NOT_RUN','None']
                report['architecture']='Not reported';checks['nativeHelper']=['fail','INVALID_RESULT','None']
                return validate(report)
            known=report['model']==MODEL and report['firmware']==FIRMWARE[8:].rstrip(';') and report['architecture']=='ARM32' and checks['identity']==['pass','OK','SDK']
            report['profile']='known' if known else 'needs-review'
            if not known: checks['homeSetup']=['skipped','PROFILE_NEEDED','None']
            return validate(report)
        finally:
            if connection is not None:
                try: connection.close()
                except Exception: pass
