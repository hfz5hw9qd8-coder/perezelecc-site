#!/usr/bin/env python3
import json, os, re, secrets, sqlite3
from datetime import datetime, date, time, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(ROOT,"data","perezelecc.db")
HOST="127.0.0.1"; PORT=8000
ADMIN_KEY=os.environ.get("PEREZELECC_ADMIN_KEY","change-moi-avant-utilisation")
TOKENS=set()
SERVICES={"Dépannage":1,"Installation électrique":2,"Rénovation électrique":4,"Mise en conformité":2,"Borne de recharge":2,"Autre":1}
OPEN_HOUR=8; CLOSE_HOUR=18

os.makedirs(os.path.dirname(DB),exist_ok=True)
con=sqlite3.connect(DB); con.execute("""CREATE TABLE IF NOT EXISTS bookings(
id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT,
service TEXT NOT NULL, notes TEXT, booking_date TEXT NOT NULL, start_time TEXT NOT NULL,
duration INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'Confirmée', created_at TEXT NOT NULL)"""); con.commit(); con.close()

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def clean(v,n=500): return re.sub(r"[\x00-\x1f]","",str(v or "")).strip()[:n]
def valid_date(s):
    try: datetime.strptime(s,"%Y-%m-%d"); return True
    except: return False
def occupied(c,d):
    return [(r["start_time"],r["duration"]) for r in c.execute("SELECT start_time,duration FROM bookings WHERE booking_date=? AND status!='Annulée'",(d,))]
def slots_for(d):
    c=db(); occ=occupied(c,d); c.close()
    out=[]; cur=datetime.combine(date.today(),time(OPEN_HOUR)); end=datetime.combine(date.today(),time(CLOSE_HOUR))
    while cur<end:
        st=cur.strftime("%H:%M"); out.append(st) if all(st!=x for x,_ in occ) else None
        cur+=timedelta(hours=1)
    return out
def send(h,code,obj):
    b=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(code); h.send_header("Content-Type","application/json; charset=utf-8"); h.send_header("Content-Length",str(len(b))); h.send_header("Access-Control-Allow-Origin","*"); h.end_headers(); h.wfile.write(b)

class Handler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self): self.send_response(204); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type, X-Admin-Key"); self.end_headers()
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=="/api/slots":
            d=parse_qs(p.query).get("date",[""])[0]
            if not valid_date(d): return send(self,400,{"error":"Date invalide."})
            return send(self,200,{"date":d,"slots":slots_for(d)})
        if p.path=="/api/admin/bookings":
            key=self.headers.get("X-Admin-Key","")
            if key!=ADMIN_KEY: return send(self,401,{"error":"Accès administrateur requis."})
            c=db(); rows=[dict(r) for r in c.execute("SELECT * FROM bookings ORDER BY booking_date,start_time")]; c.close()
            return send(self,200,{"bookings":rows})
        return super().do_GET()
    def do_POST(self):
        p=urlparse(self.path)
        if p.path=="/api/bookings":
            try:
                n=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(n))
                name=clean(data.get("name"),120); phone=clean(data.get("phone"),40); email=clean(data.get("email"),120)
                service=clean(data.get("service"),80); notes=clean(data.get("notes"),500); d=clean(data.get("date"),10); st=clean(data.get("time"),5)
                if not name or not phone or not valid_date(d) or st not in slots_for(d) or service not in SERVICES: return send(self,400,{"error":"Informations de réservation invalides ou créneau déjà pris."})
                dur=SERVICES[service]; c=db()
                # Check the whole duration, not only the first hour.
                cur=datetime.strptime(st,"%H:%M"); end=cur+timedelta(hours=dur)
                if end.hour> CLOSE_HOUR or any(t==x.strftime("%H:%M") for x,_ in occupied(c,d) for x in [datetime.strptime(t,"%H:%M") for t in [x]] if False):
                    c.close(); return send(self,409,{"error":"Ce créneau n'est plus disponible."})
                for x,_ in occupied(c,d):
                    ot=datetime.strptime(x,"%H:%M")
                    if cur < ot+timedelta(hours=1) and ot < end:
                        c.close(); return send(self,409,{"error":"Ce créneau n'est plus disponible."})
                c.execute("INSERT INTO bookings(name,phone,email,service,notes,booking_date,start_time,duration,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(name,phone,email,service,notes,d,st,dur,datetime.now().isoformat(timespec="seconds"))); c.commit(); bid=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.close()
                return send(self,201,{"ok":True,"id":bid,"message":"Votre demande d'intervention est enregistrée."})
            except Exception as e: return send(self,400,{"error":"Impossible d'enregistrer la réservation."})
        return send(self,404,{"error":"Endpoint inconnu."})

if __name__=="__main__":
    print(f"PEREZELECC — http://localhost:{PORT}")
    print("Admin key: définissez PEREZELECC_ADMIN_KEY avant de lancer le serveur.")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
