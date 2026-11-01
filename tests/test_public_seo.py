import os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]

def test_public_routes():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    with tempfile.TemporaryDirectory() as directory:
        env={**os.environ,'HIRED_DATA_DIR':directory,'HIRED_HOST':'127.0.0.1',
             'HIRED_PORT':str(port),'HIRED_PUBLIC_URL':'https://hired.example',
             'HIRED_USD_BANK_VERIFIED':'1','HIRED_BANK_ACCOUNT_NAME':'TEST ONLY',
             'HIRED_BANK_ACCOUNT_NUMBER':'TEST-NO-REAL-ACCOUNT'}
        p=subprocess.Popen([sys.executable,'server.py'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(60):
                try:
                    with urlopen(f'http://127.0.0.1:{port}/robots.txt',timeout=.3) as resp:
                        if resp.status==200:break
                except OSError:time.sleep(.08)
            else:raise AssertionError('Server did not start')
            for path,fragment in [('/','https://hired.example/'),('/resume-builder','https://hired.example/resume-builder'),
                                  ('/application-letter-maker','https://hired.example/application-letter-maker'),
                                  ('/robots.txt','Sitemap: https://hired.example/sitemap.xml'),
                                  ('/sitemap.xml','https://hired.example/application-letter-maker')]:
                with urlopen(f'http://127.0.0.1:{port}{path}') as resp:
                    text=resp.read().decode()
                    assert resp.status==200
                    assert fragment in text
        finally:
            p.terminate();p.wait(timeout=3)
