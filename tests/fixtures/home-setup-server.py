"""Local-only browser fixture: no developer transport or real TV."""
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/home-setup'))
from reports import new_report
spec = importlib.util.spec_from_file_location('home_setup_page', ROOT / 'tools/home-setup/setup.py')
page = importlib.util.module_from_spec(spec)
spec.loader.exec_module(page)


class FakeCompanion:
    active = False
    original = False
    def perform(self, host, action):
        time.sleep(.12)
        if host != 'TV_FIXTURE': raise ValueError('TV not supported by this setup profile.')
        if action == 'inspect': return {'model':'EXAMPLE_TV','firmware':'TEST','canApply':not self.active,'canUndo':self.original,'active':self.active,'phase':'active' if self.active else 'original','recovery':'PRIVATE_LOCAL_RECOVERY'}
        self.original = True
        self.active = action == 'apply'
        return {'success':True,'message':'Clean Home setup verified.' if self.active else 'Original Samsung Home restored.'}


class FakeDiagnostics:
    def run(self, host):
        report = new_report()
        report['model'] = 'EXAMPLE_TV'
        report['profile'] = 'known' if host == 'TV_FIXTURE' else 'needs-review'
        report['checks']['metadata'] = ['pass','OK','None']
        report['checks']['homeOperation'] = ['unavailable','MISSING_SYMBOL','None'] if host != 'TV_FIXTURE' else ['pass','OK','Samsung']
        if host != 'TV_FIXTURE': report['checks']['homeSetup'] = ['skipped','PROFILE_NEEDED','None']
        return report


def fake_sender(report):
    time.sleep(.12)
    return 'CH-00000000-0000-0000-0000-000000000000'

server = page.create_server(FakeCompanion(), FakeDiagnostics(), fake_sender)
print('http://127.0.0.1:'+str(server.server_port), flush=True)
server.serve_forever()
