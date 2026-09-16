#!/usr/bin/env python3
"""
NutrioBox Vehicle Monitoring — daily report automation.

Runs on your PC (Windows Task Scheduler). Each run it:
  1. logs into OneLap (Traccar API) with your credentials
  2. pulls today's trips for every vehicle that ran
  3. detects stops, maps them to NutrioBox outlets, reverse-geocodes checkpoints
  4. builds the Excel movement report (reports\Vehicle_Movement_Report_<date>.xlsx)
  5. merges the day into public\vehicle-monitoring-data.json (dashboard date-filter history)
  6. git commit + push  (Railway auto-deploys the site)
  7. emails the Excel report to the recipients

Configure secrets in  vehicle_report_config.py  (see the .example file). Never commit that file.
"""
import os, sys, json, math, time, subprocess, datetime, smtplib, ssl, mimetypes
from email.message import EmailMessage
import urllib.parse
try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests openpyxl")
import openpyxl, copy
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.cell.cell import MergedCell

# ---------- config ----------
import re as _re
HERE = os.path.dirname(os.path.abspath(__file__))

class _Cfg: pass
def _load_config():
    path=os.path.join(HERE,"vehicle_report_config.py")
    if not os.path.exists(path):
        alt=os.path.join(HERE,"vehicle_report_config.txt")
        path = alt if os.path.exists(alt) else path
    if not os.path.exists(path):
        sys.exit("Missing vehicle_report_config.py — copy vehicle_report_config.example.py and fill it in.")
    raw={}
    for line in open(path,encoding="utf-8",errors="ignore"):
        st=line.strip()
        if not st or st.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1)
        k=k.strip()
        if not _re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k): continue
        v=_re.sub(r"\s{2,}#.*$","",v).strip()      # drop trailing "   # comment"
        v=v.replace('"','').replace("'","").strip() # tolerate any/extra quotes
        raw[k.upper()]=v
    c=_Cfg()
    c.ONELAP_EMAIL=(raw.get("ONELAP_EMAIL") or raw.get("ONELAP_NUMBER") or raw.get("ONELAP_NUMBER2")
                    or raw.get("ONELAP_number") or raw.get("ONELAP_LOGIN") or "")
    c.ONELAP_PASSWORD=raw.get("ONELAP_PASSWORD","")
    su=raw.get("SMTP_USER","")
    c.SMTP_USER=None if (not su or su.lower()=="none") else su
    c.SMTP_APP_PASSWORD=raw.get("SMTP_APP_PASSWORD","")
    emails=_re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", raw.get("EMAIL_TO",""))
    c.EMAIL_TO=emails or ["mayank@nutriobox.com"]
    return c
CFG=_load_config()

BASE       = "https://web.onelap.in"
REPO       = os.path.abspath(os.path.join(HERE, "..", ".."))
DATA_JSON  = os.path.join(REPO, "public", "vehicle-monitoring-data.json")
TEMPLATE   = os.path.join(HERE, "vehicle_movement_template.xlsx")
REPORTS    = os.path.join(REPO, "reports"); os.makedirs(REPORTS, exist_ok=True)
DEPOT      = (28.6221, 77.3787)
DEPOT_NAME = "NutrioBox (Noida 63) – Depot"
STOP_MIN   = 15          # minutes; gaps >= this are delivery stops, shorter = traffic
MIN_KM     = 5           # vehicle counts as "active" if it drove at least this
NEAR_OUTLET= 1800        # metres; stop within this of an outlet gets that outlet's name

OUTLETS = {
 "NutrioBox (Shivalik)":            (28.5335, 77.2100),
 "NutrioBox (Sector 15, Gurugram)": (28.4535, 77.0411),
 "NutrioBox (DLF Phase 2)":         (28.4839, 77.0846),
 "NutrioBox (Prashant Vihar)":      (28.7155, 77.1400),
 "NutrioBox (Janakpuri)":           (28.6211, 77.0911),
 "NutrioBox (Karkardooma)":         (28.6536, 77.2958),
 "NutrioBox (Dwarka)":              (28.5975, 77.0424),
 "NutrioBox (Rajinder Nagar)":      (28.6380, 77.1870),
 "NutrioBox (Noida)":               (28.5000, 77.4100),
}

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
def log(*a): print(datetime.datetime.now(IST).strftime("%H:%M:%S"), *a, flush=True)

# ---------- helpers ----------
def hav(a,b,c,d):
    R=6371000.0; p=math.pi/180
    x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return R*2*math.asin(math.sqrt(x))
def to_ist(iso):
    iso=iso.replace("Z","+00:00")
    if iso.endswith("+0000"): iso=iso[:-5]+"+00:00"
    return datetime.datetime.fromisoformat(iso).astimezone(IST)
def hhmm(dt): return dt.strftime("%H:%M")
def hm(mins): m=int(round(mins)); return f"{m//60}h {m%60:02d}m"

# ---------- OneLap API ----------
def onelap_session():
    s=requests.Session()
    email=(getattr(CFG,"ONELAP_EMAIL",None) or getattr(CFG,"ONELAP_NUMBER",None)
           or getattr(CFG,"ONELAP_Number",None) or getattr(CFG,"ONELAP_number",None) or "")
    pw=getattr(CFG,"ONELAP_PASSWORD","")
    r=s.post(BASE+"/api/session", data={"email":str(email),"password":str(pw)}, timeout=30)
    if r.status_code!=200: sys.exit(f"OneLap login failed: HTTP {r.status_code} {r.text[:120]}")
    log("Logged into OneLap as", r.json().get("name"))
    return s

def api(s, path, **params):
    r=s.get(BASE+path, params=params, headers={"Accept":"application/json"}, timeout=90)
    r.raise_for_status()
    return r.json()

# ---------- geocoding (Nominatim) ----------
_geocache={}
def reverse(lat,lon):
    key=f"{lat:.5f},{lon:.5f}"
    if key in _geocache: return _geocache[key]
    try:
        r=requests.get("https://nominatim.openstreetmap.org/reverse",
            params={"format":"jsonv2","lat":lat,"lon":lon,"zoom":16,"addressdetails":1},
            headers={"User-Agent":"NutrioBox-VehicleReport/1.0 (ops@nutriobox.com)"}, timeout=30)
        a=r.json().get("address",{})
        road=a.get("road",""); sub=a.get("suburb") or a.get("neighbourhood") or a.get("residential") or a.get("quarter") or a.get("city_district") or ""
        town=a.get("town") or a.get("city") or a.get("state_district") or ""
        label=", ".join([x for x in (road,sub,town) if x]) or key
        locality=sub or (road.split()[0] if road else town) or key
    except Exception as e:
        label=key; locality=key
    time.sleep(1.1)  # respect Nominatim rate limit
    _geocache[key]=(label,locality)
    return _geocache[key]

def nearest_outlet(lat,lon):
    best=None;bd=1e18
    for n,(a,b) in OUTLETS.items():
        d=hav(lat,lon,a,b)
        if d<bd:bd=d;best=n
    return best,bd

# ---------- pipeline ----------
def pos_at(trips,t):
    for tr in trips:
        if tr["s"]<=t<=tr["e"]:
            f=(t-tr["s"])/max(tr["e"]-tr["s"],1)
            return (tr["sla"]+(tr["ela"]-tr["sla"])*f, tr["slo"]+(tr["elo"]-tr["slo"])*f)
    prev=None
    for tr in trips:
        if tr["e"]<=t: prev=tr
    return (prev["ela"],prev["elo"]) if prev else (trips[0]["sla"],trips[0]["slo"])

def process_vehicle(name, rows, now_ts, summary_km):
    T=[dict(s=to_ist(r[0]).timestamp(), e=to_ist(r[1]).timestamp(),
            sla=r[2],slo=r[3],ela=r[4],elo=r[5],km=r[6]/1000.0) for r in rows]
    T.sort(key=lambda t:t["s"])
    stops=[]
    for i in range(len(T)-1):
        stops.append(dict(lat=T[i]["ela"],lon=T[i]["elo"],arr=T[i]["e"],dep=T[i+1]["s"],
                          dwell=round((T[i+1]["s"]-T[i]["e"])/60)))
    last=T[-1]
    back=hav(last["ela"],last["elo"],DEPOT[0],DEPOT[1])<1300
    stops.append(dict(lat=last["ela"],lon=last["elo"],arr=last["e"],dep=None,
                      dwell=round((now_ts-last["e"])/60),cur=not back))
    dispatch=stops[0]["dep"]
    ret=last["e"] if back else None
    body=stops[1:len(stops)-1] if back else stops[1:]
    deliveries=[x for x in body if (x.get("dwell",0)>=STOP_MIN or x.get("cur"))]
    # name each delivery
    for x in deliveries:
        on,od=nearest_outlet(x["lat"],x["lon"])
        if od<=NEAR_OUTLET:
            x["name"]=on
        else:
            _,loc=reverse(x["lat"],x["lon"]); x["name"]=f"{loc} (not a listed outlet)"
    seq=[dict(lat=DEPOT[0],lon=DEPOT[1],dep=dispatch,depot=True)]+deliveries
    if back: seq.append(dict(lat=DEPOT[0],lon=DEPOT[1],arr=ret,depot=True))
    legs=[]
    for k in range(len(seq)-1):
        a=seq[k];b=seq[k+1];disp=a["dep"];reached=b["arr"]
        cps=[]
        for mm in (30,60,90,120):
            tt=disp+mm*60
            if reached and tt<reached-120:
                pla,plo=pos_at(T,tt); lab,_=reverse(pla,plo)
                cps.append([lab, hhmm(datetime.datetime.fromtimestamp(tt,IST))])
            else:
                cps.append(None)
        fin = DEPOT_NAME if b.get("depot") else b["name"]
        travel=round(((reached if reached else now_ts)-disp)/60)
        halt = "—" if b.get("depot") else hm(b["dwell"])
        if b.get("depot"): rem="Returned to Noida 63 depot – end of route"
        elif b.get("cur"): rem=f"Currently here (as of report time) – not yet returned to depot"
        elif "(not a listed outlet)" in fin: rem=f"Stop {hm(b['dwell'])} – not in 10-outlet master list (confirm name)"
        else: rem=f"Outlet reached – halt {hm(b['dwell'])} at outlet"
        start=DEPOT_NAME if a.get("depot") else a["name"]
        legs.append([start,fin,hhmm(datetime.datetime.fromtimestamp(disp,IST)),
                     cps[0],cps[1],cps[2],cps[3],fin,hm(travel),halt,rem])
    drive=sum(round(((seq[k+1]["arr"] if seq[k+1].get("arr") else now_ts)-seq[k]["dep"])/60) for k in range(len(seq)-1))
    halt=sum(x["dwell"] for x in deliveries)
    V=dict(name=name.strip(), dist=round(summary_km,1), drive=drive, halt=halt,
           dispatch=hhmm(datetime.datetime.fromtimestamp(dispatch,IST)),
           ret=hhmm(datetime.datetime.fromtimestamp(ret,IST)) if ret else hhmm(datetime.datetime.fromtimestamp(now_ts,IST)),
           stillOut=not back)
    return V, legs, deliveries

# ---------- Excel ----------
def build_excel(date_label, devices, out_path):
    wb=openpyxl.load_workbook(TEMPLATE)
    template=wb[wb.sheetnames[0]]
    thin=Side(style='thin',color='000000'); bd=Border(left=thin,right=thin,top=thin,bottom=thin)
    arb=Font(name='Arial',size=9,bold=True); ar=Font(name='Arial',size=9)
    arc=Alignment(wrap_text=True,vertical='center',horizontal='center'); arl=Alignment(wrap_text=True,vertical='center',horizontal='left')
    def grab(ws,c): x=ws[c]; return (copy.copy(x.font),copy.copy(x.border),copy.copy(x.alignment))
    def fill(ws,dev):
        V,legs,deliveries=dev
        tf,tb,ta=grab(ws,'E8'); gf,gb,ga=grab(ws,'G8'); uf,ub,ua=grab(ws,'U8')
        ws['A6']=f"Date:  {date_label}    (device: {V['name']} · source: OneLap · dispatch {V['dispatch']} → {'returned '+V['ret'] if not V['stillOut'] else 'still out, last seen '+V['ret']})"
        for m in list(ws.merged_cells.ranges):
            if 8<=m.min_row<=33: ws.unmerge_cells(str(m))
        for r in range(8,46):
            for c in range(1,22):
                cell=ws.cell(row=r,column=c)
                if not isinstance(cell,MergedCell): cell.value=None
        center={1,7,9,11,13,15,17,19,20}; r=8
        for i,L in enumerate(legs,1):
            start,fin,disp,c30,c60,c90,c120,reached,travel,halt,rem=L
            def cp(c): return (c[0],c[1]) if c else ('','')
            vals=[i,V['name'],'','',start,fin,disp,cp(c30)[0],cp(c30)[1],cp(c60)[0],cp(c60)[1],cp(c90)[0],cp(c90)[1],cp(c120)[0],cp(c120)[1],'','',reached,travel,halt,rem]
            for c,v in enumerate(vals,1):
                cell=ws.cell(row=r,column=c,value=v)
                if c==21: cell.font=copy.copy(uf);cell.border=copy.copy(ub);cell.alignment=copy.copy(ua)
                elif c in center: cell.font=copy.copy(gf);cell.border=copy.copy(gb);cell.alignment=copy.copy(ga)
                else: cell.font=copy.copy(tf);cell.border=copy.copy(tb);cell.alignment=copy.copy(ta)
            ws.row_dimensions[r].height=40; r+=1
        tr=r
        for m in list(ws.merged_cells.ranges):
            if m.min_row==tr: ws.unmerge_cells(str(m))
        ws.merge_cells(start_row=tr,start_column=1,end_row=tr,end_column=18)
        ws.cell(row=tr,column=1,value=f"TOTAL FOR THE DAY  ({V['name']} · {len(legs)} legs · {len(deliveries)} stops)")
        ws.cell(row=tr,column=19,value=hm(V['drive'])); ws.cell(row=tr,column=20,value=hm(V['halt']))
        ws.cell(row=tr,column=21,value=f"Total distance ≈ {V['dist']} km (OneLap)")
        for c in range(1,22):
            cell=ws.cell(row=tr,column=c)
            if isinstance(cell,MergedCell): continue
            cell.font=arb; cell.border=bd
            cell.alignment=Alignment(vertical='center',horizontal='right') if c==1 else (arl if c==21 else arc)
        ws.row_dimensions[tr].height=24
    order=[d[0]['name'] for d in devices]
    for idx,dev in enumerate(devices):
        ws=template if idx==0 else wb.copy_worksheet(template)
        ws.title=dev[0]['name'][:31]; fill(ws,dev)
    for extra in list(wb.sheetnames):
        if extra not in order:
            try: del wb[extra]
            except: pass
    wb._sheets.sort(key=lambda s: order.index(s.title) if s.title in order else 99)
    for ws in wb.worksheets: ws.sheet_state='visible'
    wb.active=0
    wb.save(out_path)

# ---------- data json ----------
def merge_data_json(date_key, depot, window, Vs, LEGS):
    data={}
    if os.path.exists(DATA_JSON):
        try: data=json.load(open(DATA_JSON,encoding='utf-8'))
        except: data={}
    data[date_key]={"depot":depot,"window":window,"V":Vs,"LEGS":LEGS}
    json.dump(data, open(DATA_JSON,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))

# ---------- git ----------
def git_push(files, msg):
    def g(*a): return subprocess.run(["git",*a], cwd=REPO, capture_output=True, text=True)
    for lk in (".git/index.lock",".git/HEAD.lock"):
        p=os.path.join(REPO,lk)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass
    g("add",*files)
    c=g("-c","user.email=mayank@nutriobox.com","-c","user.name=NutrioBox","commit","-m",msg)
    if "nothing to commit" in (c.stdout+c.stderr): log("git: nothing to commit"); return
    p=g("push","origin","main")
    log("git push:", (p.stdout+p.stderr).strip()[-200:])

# ---------- email ----------
def send_email(subject, body, attachments):
    if not getattr(CFG,"SMTP_USER",None): log("email: SMTP not configured, skipping"); return
    m=EmailMessage(); m["From"]=CFG.SMTP_USER; m["To"]=", ".join(CFG.EMAIL_TO); m["Subject"]=subject
    m.set_content(body)
    for path in attachments:
        if not os.path.exists(path): continue
        ctype,_=mimetypes.guess_type(path); maintype,subtype=(ctype or "application/octet-stream").split("/",1)
        with open(path,"rb") as f: m.add_attachment(f.read(),maintype=maintype,subtype=subtype,filename=os.path.basename(path))
    with smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context()) as smtp:
        smtp.login(CFG.SMTP_USER, CFG.SMTP_APP_PASSWORD); smtp.send_message(m)
    log("email sent to", ", ".join(CFG.EMAIL_TO))

# ---------- main ----------
def main():
    override=sys.argv[1] if len(sys.argv)>1 else None   # optional YYYY-MM-DD
    now=datetime.datetime.now(IST)
    day = datetime.datetime.strptime(override,"%Y-%m-%d").replace(tzinfo=IST) if override else now
    date_key=day.strftime("%Y-%m-%d")
    frm=day.replace(hour=0,minute=0,second=0,microsecond=0).astimezone(datetime.timezone.utc).isoformat()
    to =(now if not override else day.replace(hour=23,minute=59)).astimezone(datetime.timezone.utc).isoformat()
    log("Report for", date_key, "window", frm, "->", to)

    s=onelap_session()
    devices=api(s,"/api/devices")
    Vs=[]; LEGS={}; excel_devices=[]
    for d in sorted(devices,key=lambda x:x["name"].lower()):
        did=d["id"]; nm=d["name"].strip()
        summ=api(s,"/api/reports/summary",deviceId=did,**{"from":frm,"to":to})
        km=(summ[0]["distance"]/1000.0) if summ else 0
        if km<MIN_KM:
            log(f"  skip {nm}: {km:.1f} km (no run)"); continue
        trips=api(s,"/api/reports/trips",deviceId=did,**{"from":frm,"to":to})
        if not trips: log(f"  skip {nm}: no trips"); continue
        rows=[[t["startTime"],t["endTime"],t["startLat"],t["startLon"],t["endLat"],t["endLon"],t["distance"],t["duration"]/1000.0] for t in trips]
        log(f"  {nm}: {km:.1f} km, {len(rows)} trips — processing")
        V,legs,deliveries=process_vehicle(nm,rows,now.timestamp(),km)
        Vs.append(V); LEGS[V["name"]]=legs; excel_devices.append((V,legs,deliveries))
    if not Vs: sys.exit("No active vehicles today — nothing to report.")

    window=("Full day to "+hhmm(now)+" IST") if not override else "Full day"
    date_label=day.strftime("%d %B %Y")
    merge_data_json(date_key, DEPOT_NAME, window, Vs, LEGS)
    log("data json updated:", DATA_JSON)
    xlsx=os.path.join(REPORTS, f"Vehicle_Movement_Report_{date_key}.xlsx")
    build_excel(date_label, excel_devices, xlsx); log("excel:", xlsx)

    git_push(["public/vehicle-monitoring-data.json", "public/vehicle-monitoring-dashboard.html"],
             f"Vehicle monitoring: {date_key} daily report")
    summary="\n".join(f"• {v['name']}: {v['dist']}km, dispatch {v['dispatch']}, "
                      f"{'still out' if v['stillOut'] else 'returned '+v['ret']}, "
                      f"{len(LEGS[v['name']])-(0 if v['stillOut'] else 1)} stops" for v in Vs)
    try:
        send_email(f"NutrioBox Vehicle Report — {date_label}",
                   f"Attached: today's vehicle movement report.\n\n{summary}\n\n"
                   f"Live dashboard: https://opsdashboard.nutriobox.com/dashboard/vehicle-monitoring\n",
                   [xlsx])
    except Exception as e:
        log("email step failed (report still saved & pushed):", e)
    log("DONE.")

if __name__=="__main__":
    main()
