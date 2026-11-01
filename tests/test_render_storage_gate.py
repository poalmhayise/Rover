import os, socket, subprocess, sys, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]

def test_render_never_uses_ephemeral_sqlite_for_customer_orders(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env={**os.environ,'RENDER':'true','HIRED_DATA_DIR':str(tmp_path/'ephemeral'),
        'HIRED_HOST':'127.0.0.1','HIRED_PORT':str(port),'HIRED_USD_BANK_VERIFIED':'1',
        'HIRED_BANK_ACCOUNT_NAME':'Example Holder','HIRED_BANK_ACCOUNT_NUMBER':'test-only',
        'HIRED_ADMIN_PASSWORD':'test password','HIRED_SECRET_KEY':'test secret',
        'HIRED_SUPPORT_EMAIL':'help@example.test','HIRED_PERSISTENT_STORAGE_CONFIRMED':'1'}
    env.pop('HIRED_DATABASE_URL',None)
    proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
        for _ in range(80):
            try:r=requests.get(f'http://127.0.0.1:{port}/api/config',timeout=.2)
            except requests.RequestException:time.sleep(.06);continue
            if r.status_code==200:break
        else:raise AssertionError('Server did not start')
        assert r.json()['ready'] is False
        resp=requests.post(f'http://127.0.0.1:{port}/api/orders',json={},timeout=3)
        assert resp.status_code==503
    finally:
        proc.terminate();proc.wait(timeout=3)
