#!/usr/bin/env python3
import json, os, re, sqlite3
from datetime import datetime, date, time, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(ROOT,"data","perezelecc.db")
HOST="127.0.0.1"; PORT=8000
ADMIN_KEY=os.environ.get("PEREZELECC_ADMIN_KEY","decembre10")
SERVICES={"Dépannage":1,"Installation électrique":2,"Rénovation électrique":4,"Mise en conformité":2,"Borne de recharge":2,"Autre":1}
OPEN_HOUR=8; CLOSE_HOUR=18; SLOT_MINUTES=60
os.makedirs(os.path.dirname(DB),exist_ok=True)

def init_db():
    c=sqlite3.connect(DB); c.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT NOT NULL,email TEXT,
        service TEXT NOT NULL,notes TEXT,booking_date TEXT NOT NULL,start_time TEXT NOT NULL,
        duration INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'Confirmée',created_at TEXT NOT NULL)"""); c.commit(); c.close()
init_db()

def db():
    c=sqlite3.connect(DB,timeout=10); c.row_factory=sqlite3.Row; return c
def clean(v,n=500): return re.sub(r"[\x00-\x1f\x7f]","",str(v or "")).strip()[:n]
def valid_date(s):
    try: datetime.strptime(s,"%Y-%m-%d"); return True
    except (TypeError,ValueError): return False
def parse_dt(s): return datetime.strptime(s,"%H:%M")
def occupied(c,day):
    rows=c.execute("SELECT start_time,duration FROM bookings WHERE booking_date=? AND status!='Annulée'",(day,)).fetchall()
    return [(parse_dt(r["start_time"]),int(r["duration"])) for r in rows]
def interval_free(start,duration,busy):
    end=start+timedelta(hours=duration)
    return all(not (start < bs+timedelta(hours=bd) and bs < end) for bs,bd in busy)
def slots_for(day,service="Autre"):
    duration=SERVICES.get(service,1); c=db(); busy=occupied(c,day); c.close()
    out=[]; cur=datetime.combine(date.today(),time(OPEN_HOUR)); close=datetime.combine(date.today(),time(CLOSE_HOUR))
    while cur+timedelta(hours=duration)<=close:
        if interval_free(cur,duration,busy): out.append(cur.strftime("%H:%M"))
        cur+=timedelta(minutes=SLOT_MINUTES)
    return out
def send(h,code,obj):
    b=json.dumps(obj,ensure_ascii=False).encode(); h.send_response(code)
    h.send_header("Content-Type","application/json; charset=utf-8"); h.send_header("Content-Length",str(len(b)))
    h.send_header("Cache-Control","no-store"); h.send_header("Access-Control-Allow-Origin","*")
    h.send_header("Access-Control-Allow-Headers","Content-Type, X-Admin-Key"); h.end_headers(); h.wfile.write(b)

class Handler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type, X-Admin-Key")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS"); self.end_headers()
    def do_GET(self):
        try:
            p=urlparse(self.path)
            if p.path=="/api/health": return send(self,200,{"ok":True,"service":"PEREZELECC calendrier"})
            if p.path=="/api/slots":
                q=parse_qs(p.query); day=q.get("date",[""])[0]; service=clean(q.get("service",["Autre"])[0],80)
                if not valid_date(day): return send(self,400,{"error":"Date invalide."})
                if service not in SERVICES: service="Autre"
                return send(self,200,{"date":day,"service":service,"duration":SERVICES[service],"slots":slots_for(day,service)})
            if p.path=="/api/admin/bookings":
                if self.headers.get("X-Admin-Key","")!=ADMIN_KEY: return send(self,401,{"error":"Clé administrateur incorrecte."})
                c=db(); rows=[dict(r) for r in c.execute("SELECT * FROM bookings ORDER BY booking_date,start_time").fetchall()]; c.close()
                return send(self,200,{"bookings":rows})
            return super().do_GET()
        except Exception as e: return send(self,500,{"error":"Erreur serveur.","detail":str(e)})
    def do_POST(self):
        try:
            if urlparse(self.path).path!="/api/bookings": return send(self,404,{"error":"Endpoint inconnu."})
            n=int(self.headers.get("Content-Length","0")); data=json.loads(self.rfile.read(n) or b"{}")
            name=clean(data.get("name"),120); phone=clean(data.get("phone"),40); email=clean(data.get("email"),120)
            service=clean(data.get("service"),80); notes=clean(data.get("notes"),500); day=clean(data.get("date"),10); st=clean(data.get("time"),5)
            if not name or not phone: return send(self,400,{"error":"Nom et téléphone obligatoires."})
            if service not in SERVICES: return send(self,400,{"error":"Type d'intervention invalide."})
            if not valid_date(day): return send(self,400,{"error":"Date invalide."})
            try: start=parse_dt(st)
            except ValueError: return send(self,400,{"error":"Horaire invalide."})
            duration=SERVICES[service]; opening=datetime.combine(date.today(),time(OPEN_HOUR)); closing=datetime.combine(date.today(),time(CLOSE_HOUR))
            if start<opening or start+timedelta(hours=duration)>closing: return send(self,400,{"error":"Horaire indisponible."})
            c=db(); busy=occupied(c,day)
            if not interval_free(start,duration,busy):
                c.close(); return send(self,409,{"error":"Ce créneau vient d'être réservé. Choisissez-en un autre."})
            c.execute("INSERT INTO bookings(name,phone,email,service,notes,booking_date,start_time,duration,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (name,phone,email,service,notes,day,st,duration,datetime.now().isoformat(timespec="seconds"))); c.commit()
            bid=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.close()
            return send(self,201,{"ok":True,"id":bid,"message":"Votre rendez-vous est enregistré."})
        except json.JSONDecodeError: return send(self,400,{"error":"Données JSON invalides."})
        except Exception as e: return send(self,500,{"error":"Impossible d'enregistrer le rendez-vous.","detail":str(e)})

if __name__=="__main__":
    print(f"PEREZELECC — http://localhost:{PORT}")
    print("Calendrier : 08:00–18:00")
    print("Admin : clé PEREZELECC_ADMIN_KEY disponible.")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
