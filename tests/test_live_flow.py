import base64, io, json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
import requests
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

def test_live_payment_flow(tmp_path):
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    env={**os.environ,'HIRED_DATA_DIR':str(tmp_path/'db'),'HIRED_HOST':'127.0.0.1','HIRED_PORT':str(port),
         'HIRED_BANK_ACCOUNT_NAME':'Sample Holder','HIRED_BANK_ACCOUNT_NUMBER':'TEST-ONLY-NUMBER',
         'HIRED_USD_BANK_VERIFIED':'1','HIRED_PERSISTENT_STORAGE_CONFIRMED':'1','HIRED_SUPPORT_EMAIL':'support@example.com','HIRED_ADMIN_PASSWORD':'test secure password 123456',
         'HIRED_SECRET_KEY':'test key test key test key 1234567890','HIRED_HTTPS_ONLY':'0'}
    proc=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    base=f'http://127.0.0.1:{port}'
    try:
        for i in range(75):
            if proc.poll() is not None: raise AssertionError('Server crashed: '+proc.stderr.read().decode())
            try:
                r=requests.get(base+'/api/config',timeout=.3)
                if r.status_code==200: break
            except requests.RequestException:pass
            time.sleep(.08)
        else: raise AssertionError('Could not connect to server')
        c=r.json()
        assert c['ready'] and c['bank']['accountNumber']=='TEST-ONLY-NUMBER'
        assert c['bankCurrency']=='USD' and c['priceUsd']=='0.60' and c['bankAmount']=='0.60'
        assert requests.get(base+'/').status_code==200
        assert requests.get(base+'/static/app.js').status_code==200
        data={'fullName':'Nandi Dlamini','email':'nandi@example.com','summary':'A driven and motivated candidate.', 'headline':'Office Administrator','experience':'Office team - 2024 to 2026', 'skills':'Customer care'}
        r=requests.post(base+'/api/orders',json={'type':'cv','theme':'forest','details':data},timeout=5)
        assert r.status_code==201, r.text
        order=r.json();id=order['id'];token=order['token']
        assert order['reference']=='HIRED-'+id
        assert order['amount']=='0.60' and order['currency']=='USD'
        dl=f'{base}/api/orders/{id}/download?token={token}'
        assert requests.get(dl,timeout=5).status_code==403
        im=Image.new('RGB',(200,200),(240,240,240)); stream=io.BytesIO();im.save(stream,format='JPEG')
        proof=base64.b64encode(stream.getvalue()).decode()
        r=requests.post(f'{base}/api/orders/{id}/proof',json={'token':token,'extension':'jpg','content':proof},timeout=5)
        assert r.status_code==200, r.text
        assert requests.get(dl,timeout=5).status_code==403
        sess=requests.Session()
        r=sess.post(base+'/api/admin/login',json={'password':env['HIRED_ADMIN_PASSWORD']},timeout=5)
        assert r.status_code==200, r.text
        r=sess.get(base+'/api/admin/orders',timeout=5);assert r.status_code==200
        assert r.json()['orders'][0]['status']=='awaiting_review'
        # Receipt alone is not enough. The server also requires an explicit bank-credit check.
        r=sess.post(f'{base}/api/admin/orders/{id}/approve',json={},headers={'X-Hired-Admin':'1'},timeout=5)
        assert r.status_code==409, r.text
        r=sess.post(f'{base}/api/admin/orders/{id}/approve',json={'bankCreditVerified':True,
            'reference':'HIRED-'+id},headers={'X-Hired-Admin':'1'},timeout=5)
        assert r.status_code==200, r.text
        r=requests.get(dl,timeout=5);assert r.status_code==200 and r.content.startswith(b'%PDF-')
        assert r.headers['Content-Type']=='application/pdf'
        r=sess.post(f'{base}/api/admin/orders/{id}/delete',json={},headers={'X-Hired-Admin':'1'},timeout=5)
        assert r.status_code==200
        assert requests.get(dl,timeout=5).status_code==404
    finally:
        proc.terminate()
        try:proc.wait(timeout=3)
        except subprocess.TimeoutExpired:proc.kill()
