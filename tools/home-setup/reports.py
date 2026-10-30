"""Allowlisted compatibility reports; no addresses, IDs, raw logs or settings."""
import json
import re
import urllib.request

VERSION = '1.4.3'
ENDPOINT = 'https://clean-home-feedback.perkymule6.chatgpt.site/api/reports'
STEPS = ('metadata','developer','capabilities','nativeHelper','identity','architecture','homeOperation','homePreference','startupPreference','bootingPreference','firstScreen','autoStart','lastApp','appBoot','homeSetup')
STATES = {'pass','fail','unavailable','skipped'}
CODES = {'OK','NOT_RUN','HTTP_FAILED','NOT_SAMSUNG','SDB_FAILED','CAPS_FAILED','HELPER_FAILED','NATIVE_TOOL_MISSING','CLEANUP_UNKNOWN','INVALID_RESULT','ROOT_REFUSED','UID_UNSUPPORTED','ARCH_UNSUPPORTED','MISSING_LIBRARY','MISSING_SYMBOL','ACCESS_DENIED','READ_FAILED','UNEXPECTED_VALUE','PROFILE_NEEDED','STRICT_CHECK_FAILED','NOT_CONFIRMED'}
OBSERVATIONS = {'None','Samsung','CleanHome','Other','On','Off','Available','Unavailable','Unknown','SDK'}
FIELDS = {'schema','kind','setup','model','firmware','tizen','architecture','profile','action','phase','checks'}


def clean_model(value):
    return value if isinstance(value,str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{2,39}',value) else 'Not reported'


def clean_firmware(value):
    return value if isinstance(value,str) and re.fullmatch(r'T-[A-Za-z][A-Za-z0-9_.-]{0,61}',value) and not re.search(r'(?:\d{1,3}\.){3}\d{1,3}',value) else 'Not reported'


def clean_tizen(value):
    if isinstance(value,str) and re.fullmatch(r'\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,2}',value): return '.'.join(value.split('.')[:3])
    return 'Not reported'


def new_report():
    return {'schema':2,'kind':'home-setup','setup':VERSION,'model':'Not reported','firmware':'Not reported','tizen':'Not reported','architecture':'Not reported','profile':'unknown','action':'diagnose','phase':'notChecked','checks':{name:['skipped','NOT_RUN','None'] for name in STEPS}}


def validate(report):
    if not isinstance(report,dict) or set(report)!=FIELDS or report.get('schema')!=2 or report.get('kind')!='home-setup': raise ValueError('Invalid compatibility report')
    if not isinstance(report['setup'],str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}',report['setup']): raise ValueError('Invalid setup version')
    if clean_model(report['model'])!=report['model'] or clean_firmware(report['firmware'])!=report['firmware'] or clean_tizen(report['tizen'])!=report['tizen']: raise ValueError('Invalid report metadata')
    if report['architecture'] not in {'Not reported','ARM32','ARM64','Other'} or report['profile'] not in {'known','needs-review','unknown'} or report['action'] not in {'diagnose','apply','undo'} or report['phase'] not in {'notChecked','original','active','unknown'}: raise ValueError('Invalid report state')
    checks=report['checks']
    if not isinstance(checks,dict) or set(checks)!=set(STEPS): raise ValueError('Incomplete report checks')
    for value in checks.values():
        if not isinstance(value,list) or len(value)!=3 or not isinstance(value[0],str) or not isinstance(value[1],str) or not isinstance(value[2],str) or value[0] not in STATES or value[1] not in CODES or value[2] not in OBSERVATIONS: raise ValueError('Invalid check result')
    return json.loads(json.dumps(report,separators=(',',':')))


def send(report):
    body=json.dumps(validate(report),separators=(',',':')).encode()
    if len(body)>2048: raise ValueError('Report is too large')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args): return None
    opener=urllib.request.build_opener(NoRedirect())
    request=urllib.request.Request(ENDPOINT,data=body,headers={'Content-Type':'application/json','User-Agent':'CleanHome-Setup/'+VERSION})
    try:
        with opener.open(request,timeout=10) as response:
            payload=response.read(257)
            if response.status!=201 or len(payload)>256: raise ValueError()
            result=json.loads(payload)
            if result.get('accepted') is not True or not re.fullmatch(r'CH-[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',result.get('id','')): raise ValueError()
            return result['id']
    except Exception:
        raise ValueError('Report delivery was not confirmed. You can save the report and try again later.') from None
