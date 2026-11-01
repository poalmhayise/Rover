"""Hired — a dependency-light FNB bank-transfer CV and letter storefront.

For production, place behind HTTPS reverse proxy, set all HIRED_* variables,
use an encrypted/regularly backed-up DATA_DIR, and verify bank credits manually.
"""
from __future__ import annotations
import base64, hashlib, hmac, json, mimetypes, os, re, secrets, sqlite3, time
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from html import escape as html_escape
from pdf_documents import build_pdf

ROOT=Path(__file__).resolve().parent

def load_env():
    p=ROOT/'.env'
    if p.is_file():
        for line in p.read_text(encoding='utf-8').splitlines():
            if not line.strip() or line.lstrip().startswith('#') or '=' not in line: continue
            key,value=line.split('=',1)
            os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
load_env()
DATA=Path(os.getenv('HIRED_DATA_DIR',str(ROOT/'data'))).resolve()
DATA.mkdir(parents=True,exist_ok=True)
PROOFS=DATA/'payment_proofs'
PROOFS.mkdir(parents=True,exist_ok=True)
DB=DATA/'hired.sqlite3'
SECRET=os.getenv('HIRED_SECRET_KEY','')
ADMIN_PASSWORD=os.getenv('HIRED_ADMIN_PASSWORD','')
HTTPS_ONLY=os.getenv('HIRED_HTTPS_ONLY','0')=='1'
AMOUNT='0.60'  # The universal price is fixed in USD, not converted to SZL.
USD_BANK_VERIFIED=os.getenv('HIRED_USD_BANK_VERIFIED','0')=='1'
PUBLIC_URL=os.getenv('HIRED_PUBLIC_URL','').strip().rstrip('/')
if PUBLIC_URL and (not PUBLIC_URL.startswith('https://') or not urlsplit(PUBLIC_URL).hostname):
    PUBLIC_URL=''  # Never use an unverified Host header for SEO links
BANK={
    'name':'FNB Eswatini',
    'accountName':os.getenv('HIRED_BANK_ACCOUNT_NAME','').strip(),
    'accountNumber':os.getenv('HIRED_BANK_ACCOUNT_NUMBER','').strip(),
    'branch':os.getenv('HIRED_BANK_BRANCH','').strip(),
    'accountType':os.getenv('HIRED_BANK_ACCOUNT_TYPE','').strip(),
    'swift':os.getenv('HIRED_BANK_SWIFT','').strip(),
}
LOGIN_ATTEMPTS={}
PERSISTENCE_CONFIRMED=(os.getenv('HIRED_PERSISTENT_STORAGE_CONFIRMED','0')=='1' and (not os.getenv('RENDER') or os.path.ismount(DATA)))
SUPPORT_EMAIL=os.getenv('HIRED_SUPPORT_EMAIL','').strip()
READY=bool(BANK['accountName'] and BANK['accountNumber'] and USD_BANK_VERIFIED and PERSISTENCE_CONFIRMED and ADMIN_PASSWORD and SECRET and SUPPORT_EMAIL)

def db():
    con=sqlite3.connect(DB,timeout=20)
    con.row_factory=sqlite3.Row
    return con

def setup_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS orders (
           id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, doc_type TEXT NOT NULL,
           theme TEXT NOT NULL, details TEXT NOT NULL, status TEXT NOT NULL,
           bank_amount TEXT NOT NULL, created_at TEXT NOT NULL,
           proof_path TEXT DEFAULT NULL, reviewed_at TEXT DEFAULT NULL)''')
setup_db()

def token_hash(token): return hashlib.sha256(token.encode()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def safe_compare(a,b): return hmac.compare_digest(str(a),str(b))

def signed_cookie():
    if not SECRET: return None
    ts=str(int(time.time()))
    msg='hired-admin:'+ts
    signature=hmac.new(SECRET.encode(),msg.encode(),hashlib.sha256).hexdigest()
    return ts+'.'+signature

def is_admin(handler):
    if not SECRET or not ADMIN_PASSWORD: return False
    cookie=SimpleCookie()
    try: cookie.load(handler.headers.get('Cookie',''))
    except Exception: return False
    if 'hired_admin' not in cookie: return False
    try:
        ts,sig=cookie['hired_admin'].value.split('.',1)
        if abs(time.time()-int(ts))>8*3600: return False
        expected=hmac.new(SECRET.encode(),('hired-admin:'+ts).encode(),hashlib.sha256).hexdigest()
        return safe_compare(sig,expected)
    except Exception:return False

class HiredHandler(BaseHTTPRequestHandler):
    server_version='Hired/1.0'
    def log_message(self,fmt,*args):
        # Deliberately omit URLs: private customer access tokens may be in query strings.
        print('%s - %s' % (self.address_string(),fmt.split(' ')[0]))
    def headers_out(self,status=200,ctype='application/json; charset=utf-8',size=None,extra=None):
        self.send_response(status)
        self.send_header('Content-Type',ctype)
        if size is not None:self.send_header('Content-Length',str(size))
        self.send_header('Cache-Control','no-store')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy',"default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; font-src 'self'; base-uri 'none'; form-action 'self'")
        if HTTPS_ONLY:self.send_header('Strict-Transport-Security','max-age=31536000; includeSubDomains')
        for a,b in (extra or {}).items(): self.send_header(a,b)
        self.end_headers()
    def reply(self,obj,status=200,extra=None):
        body=json.dumps(obj,ensure_ascii=False).encode()
        self.headers_out(status,size=len(body),extra=extra)
        self.wfile.write(body)
    def error(self,message,status=400): self.reply({'error':message},status)
    def read_json(self):
        try: l=int(self.headers.get('Content-Length','0'))
        except ValueError: raise ValueError('Invalid request size')
        if l<2 or l>6*1024*1024: raise ValueError('Request too large or empty')
        if 'application/json' not in self.headers.get('Content-Type',''):
            raise ValueError('JSON required')
        return json.loads(self.rfile.read(l))
    def seo_markup(self,route='/'):
        if not PUBLIC_URL: return ''
        canonical=html_escape(PUBLIC_URL + (route if route!='/' else '/') , quote=True)
        return f'<link rel="canonical" href="{canonical}"><meta property="og:url" content="{canonical}">'
    def serve_page(self, filename, route):
        p=ROOT/'static'/filename
        if not p.is_file():return self.error('Not found',404)
        page=p.read_text(encoding='utf-8').replace('<!--HIRED_CANONICAL-->',self.seo_markup(route))
        body=page.encode('utf-8')
        self.headers_out(200,'text/html; charset=utf-8',len(body));self.wfile.write(body)
    def serve_static(self,p,ctype):
        if not p.is_file():return self.error('Not found',404)
        body=p.read_bytes()
        self.headers_out(200,ctype,len(body));self.wfile.write(body)
    def get_order(self,order_id):
        with db() as con: return con.execute('SELECT * FROM orders WHERE id=?',(order_id,)).fetchone()
    def authorized_order(self,order_id,token):
        row=self.get_order(order_id)
        if not row or not isinstance(token,str) or not safe_compare(row['token_hash'],token_hash(token)):
            return None
        return row
    def do_GET(self):
        parts=urlsplit(self.path)
        path=parts.path
        query=parse_qs(parts.query)
        if path in ('/','/index.html'):
            return self.serve_page('index.html','/')
        if path=='/resume-builder':return self.serve_page('resume-builder.html','/resume-builder')
        if path=='/application-letter-maker':return self.serve_page('application-letter-maker.html','/application-letter-maker')
        if path=='/robots.txt':
            robots='User-agent: *\nDisallow: /api/\nDisallow: /admin\nAllow: /\n'
            if PUBLIC_URL:robots+='Sitemap: '+PUBLIC_URL+'/sitemap.xml\n'
            body=robots.encode()
            self.headers_out(200,'text/plain; charset=utf-8',len(body))
            return self.wfile.write(body)
        if path=='/sitemap.xml':
            if not PUBLIC_URL:return self.error('Sitemap becomes available after HIRED_PUBLIC_URL is set',503)
            urls=['/','/resume-builder','/application-letter-maker']
            body=('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+html_escape(PUBLIC_URL + route)+'</loc></url>' for route in urls)+'</urlset>').encode()
            self.headers_out(200,'application/xml; charset=utf-8',len(body))
            return self.wfile.write(body)
        if path=='/admin':return self.serve_static(ROOT/'static'/'admin.html','text/html; charset=utf-8')
        if path=='/privacy':return self.serve_static(ROOT/'static'/'privacy.html','text/html; charset=utf-8')
        if path.startswith('/static/'):
            file=(ROOT/'static'/path.removeprefix('/static/')).resolve()
            if not file.is_relative_to((ROOT/'static').resolve()):return self.error('Not found',404)
            return self.serve_static(file,mimetypes.guess_type(file.name)[0] or 'application/octet-stream')
        if path=='/api/config':
            return self.reply({'brand':'Hired','priceUsd':'0.60','bankCurrency':'USD','bankAmount':AMOUNT,
              'ready':READY,'usdBankVerified':USD_BANK_VERIFIED,'bank':BANK if READY else {'name':'FNB Eswatini'},
              'supportEmail':os.getenv('HIRED_SUPPORT_EMAIL','').strip()})
        m=re.fullmatch(r'/api/orders/([A-F0-9]{12})',path)
        if m:
            row=self.authorized_order(m[1],query.get('token',[''])[0])
            if not row:return self.error('Order not found',404)
            return self.reply({'id':row['id'],'type':row['doc_type'],'status':row['status'],
                 'amount':row['bank_amount'],'currency':'USD','reference':'HIRED-'+row['id'],'ready':row['status']=='approved'})
        m=re.fullmatch(r'/api/orders/([A-F0-9]{12})/download',path)
        if m:
            row=self.authorized_order(m[1],query.get('token',[''])[0])
            if not row:return self.error('Order not found',404)
            if row['status']!='approved':return self.error('Payment has not been confirmed',403)
            try: document=build_pdf(row['doc_type'],json.loads(row['details']),row['theme'])
            except Exception:return self.error('Could not generate PDF; contact support',500)
            extra={'Content-Disposition':f'attachment; filename="Hired_{row["doc_type"]}_{row["id"]}.pdf"'}
            self.headers_out(200,'application/pdf',len(document),extra)
            return self.wfile.write(document)
        if path=='/api/admin/orders':
            if not is_admin(self):return self.error('Please sign in',401)
            with db() as con:
                rows=con.execute('SELECT id,doc_type,details,status,bank_amount,created_at,proof_path FROM orders ORDER BY created_at DESC LIMIT 300').fetchall()
            return self.reply({'orders':[{'id':r['id'],'type':r['doc_type'],
                'name':json.loads(r['details']).get('fullName',''),'email':json.loads(r['details']).get('email',''),
                'status':r['status'],'amount':r['bank_amount'],'currency':'USD','date':r['created_at'],
                'proof':bool(r['proof_path'])} for r in rows]})
        m=re.fullmatch(r'/api/admin/orders/([A-F0-9]{12})/proof',path)
        if m:
            if not is_admin(self):return self.error('Please sign in',401)
            row=self.get_order(m[1])
            if not row or not row['proof_path']:return self.error('No proof uploaded',404)
            p=(PROOFS/row['proof_path']).resolve()
            if not p.is_relative_to(PROOFS.resolve()):return self.error('Invalid file',404)
            mime={'pdf':'application/pdf','png':'image/png','jpg':'image/jpeg'}.get(p.suffix.lstrip('.'),'application/octet-stream')
            body=p.read_bytes()
            self.headers_out(200,mime,len(body),{'Content-Disposition':'attachment; filename=payment-proof'+p.suffix})
            return self.wfile.write(body)
        return self.error('Not found',404)
    def do_POST(self):
        path=urlsplit(self.path).path
        # Privileged endpoints require a custom header, preventing simple CSRF form posts.
        if path.startswith('/api/admin/') and path!='/api/admin/login' and self.headers.get('X-Hired-Admin')!='1':
            return self.error('Missing admin request header',403)
        try: payload=self.read_json()
        except (ValueError,json.JSONDecodeError) as e: return self.error(str(e))
        if not isinstance(payload,dict):return self.error('Invalid request')
        if path=='/api/orders':
            if not READY:return self.error('Bank checkout is not configured yet',503)
            kind=payload.get('type')
            theme=payload.get('theme','violet')
            details=payload.get('details')
            if kind not in ('cv','letter') or theme not in ('violet','navy','forest','coral'):
                return self.error('Invalid document or template')
            if not isinstance(details,dict):return self.error('Document details are missing')
            allowed=('fullName','email','phone','location','website','headline','summary','experience','education','skills','projects','languages','jobTitle','company','hiringManager','strengths','motivation','letterBody')
            details={k:str(details.get(k,''))[:3000].strip() for k in allowed}
            if len(json.dumps(details))>18000:return self.error('Document content is too long')
            if len(details['fullName'])<2 or '@' not in details['email'] or len(details['email'])>160:
                return self.error('Please provide your name and a valid email')
            if kind=='cv' and not (details['summary'] or details['experience'] or details['education']):
                return self.error('Add your profile, experience or education')
            if kind=='letter' and not details['jobTitle']:return self.error('Add the position you are applying for')
            order_id=secrets.token_hex(6).upper()
            token=secrets.token_urlsafe(24)
            with db() as con:
                con.execute('INSERT INTO orders(id,token_hash,doc_type,theme,details,status,bank_amount,created_at) VALUES(?,?,?,?,?,?,?,?)',
                (order_id,token_hash(token),kind,theme,json.dumps(details,ensure_ascii=False),'pending_payment',AMOUNT,now()))
            return self.reply({'id':order_id,'token':token,'status':'pending_payment','amount':AMOUNT,'currency':'USD',
                'reference':'HIRED-'+order_id,'bank':BANK},201)
        m=re.fullmatch(r'/api/orders/([A-F0-9]{12})/proof',path)
        if m:
            row=self.authorized_order(m[1],payload.get('token'))
            if not row:return self.error('Order not found',404)
            if row['status'] in ('approved','rejected'):
                return self.error('This order is already reviewed',409)
            ext=payload.get('extension')
            if ext not in ('pdf','png','jpg'):return self.error('Proof must be PDF, JPG or PNG')
            try: raw=base64.b64decode(payload.get('content',''),validate=True)
            except Exception:return self.error('Invalid proof file')
            if len(raw)<100 or len(raw)>3*1024*1024:return self.error('Proof must be under 3MB')
            if ext=='pdf' and not raw.startswith(b'%PDF-'):return self.error('Invalid PDF')
            if ext=='png' and not raw.startswith(b'\x89PNG\r\n\x1a\n'):return self.error('Invalid PNG')
            if ext=='jpg' and not raw.startswith(b'\xff\xd8\xff'):return self.error('Invalid JPG')
            filename=f'{m[1]}.{ext}'
            # Remove any earlier proof from same order when replacing it.
            if row['proof_path'] and row['proof_path']!=filename:
                (PROOFS/row['proof_path']).unlink(missing_ok=True)
            (PROOFS/filename).write_bytes(raw)
            with db() as con:
                con.execute('UPDATE orders SET proof_path=?,status=? WHERE id=?',
                           (filename,'awaiting_review',m[1]))
            return self.reply({'ok':True,'status':'awaiting_review'})
        if path=='/api/admin/login':
            if not ADMIN_PASSWORD or not SECRET:return self.error('Admin login is not configured',503)
            ip=self.client_address[0]
            cutoff=time.time()-900
            failures=[t for t in LOGIN_ATTEMPTS.get(ip,[]) if t>cutoff]
            if len(failures)>=8: return self.error('Too many sign-in attempts. Try again in 15 minutes.',429)
            pw=payload.get('password','')
            if not isinstance(pw,str) or not safe_compare(pw,ADMIN_PASSWORD):
                failures.append(time.time())
                LOGIN_ATTEMPTS[ip]=failures
                time.sleep(0.4)
                return self.error('Incorrect password',401)
            LOGIN_ATTEMPTS.pop(ip,None)
            c=signed_cookie()
            attrs=f'hired_admin={c}; HttpOnly; Path=/; SameSite=Strict; Max-Age=28800'
            if HTTPS_ONLY:attrs+='; Secure'
            return self.reply({'ok':True},extra={'Set-Cookie':attrs})
        if path=='/api/admin/logout':
            return self.reply({'ok':True},extra={'Set-Cookie':'hired_admin=; HttpOnly; Path=/; SameSite=Strict; Max-Age=0'})
        m=re.fullmatch(r'/api/admin/orders/([A-F0-9]{12})/(approve|reject|delete)',path)
        if m:
            if not is_admin(self):return self.error('Please sign in',401)
            row=self.get_order(m[1])
            if not row:return self.error('Order not found',404)
            if m[2]=='approve':
                if not row['proof_path']:return self.error('No payment proof submitted',409)
                with db() as con:con.execute('UPDATE orders SET status=?,reviewed_at=? WHERE id=?',('approved',now(),m[1]))
            elif m[2]=='reject':
                with db() as con:con.execute('UPDATE orders SET status=?,reviewed_at=? WHERE id=?',('rejected',now(),m[1]))
            else:
                if row['proof_path']:(PROOFS/row['proof_path']).unlink(missing_ok=True)
                with db() as con:con.execute('DELETE FROM orders WHERE id=?',(m[1],))
            return self.reply({'ok':True})
        return self.error('Not found',404)

def main():
    host=os.getenv('HIRED_HOST','127.0.0.1')
    port=int(os.getenv('HIRED_PORT',os.getenv('PORT','8080')))
    print(f'Hired starting at http://{host}:{port} | checkout configured: {READY} | admin configured: {bool(ADMIN_PASSWORD and SECRET)}')
    ThreadingHTTPServer((host,port),HiredHandler).serve_forever()

if __name__=='__main__':main()
