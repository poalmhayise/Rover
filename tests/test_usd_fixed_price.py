"""Guard against accidentally restoring local-currency checkout or opening USD checkout early."""
import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]

def test_usd_price_and_verification_gate():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    with tempfile.TemporaryDirectory() as temporary:
        env={**os.environ,'HIRED_DATA_DIR':temporary,'HIRED_HOST':'127.0.0.1','HIRED_PORT':str(port),
            'HIRED_BANK_ACCOUNT_NAME':'TEST HOLDER','HIRED_BANK_ACCOUNT_NUMBER':'TEST-NUMBER',
            'HIRED_USD_BANK_VERIFIED':'0','HIRED_PRICE_SZL':'99999'}
        proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        url=f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                try:
                    result=requests.get(url+'/api/config',timeout=.2)
                    if result.status_code==200:break
                except requests.RequestException:time.sleep(.05)
            else: raise AssertionError('Server did not start')
            data=result.json()
            assert data['priceUsd']=='0.60' and data['bankAmount']=='0.60'
            assert data['bankCurrency']=='USD' and data['ready'] is False
            assert requests.post(url+'/api/orders',json={'type':'cv','theme':'violet','details':{}},timeout=3).status_code==503
        finally:
            proc.terminate();proc.wait(timeout=3)
