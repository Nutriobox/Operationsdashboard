"""
Daily Sales row -> the REAL .xlsx "Sales Data", written via the Google DRIVE API.

Why this exists: the "Sales Data" workbook the directors share is an uploaded
Excel (.xlsx). The Sheets API can't edit Office files, so the old path typed into
the sheet through a signed-in Chrome profile — a login that keeps expiring. The
Drive API *can* replace the .xlsx file's bytes in place (same file, same sharing),
using the service-account key, which never logs out. So this job needs NO browser
and NO Google login:

    Petpooja (HTTP, cookie)  ->  build B..U  ->  Drive download .xlsx
      ->  surgically edit ONLY the target day's row (all else byte-identical)
      ->  Drive files.update  ->  verify.

  python daily_sheet_drive.py                 fill YESTERDAY's row (scheduled use)
  python daily_sheet_drive.py --date 2026-09-28
  python daily_sheet_drive.py --dry-run       pull + locate row + preview, no upload
  python daily_sheet_drive.py --force         overwrite a row that already has data

Guards: outlet totals must sum to Total Sales; the target row must already carry
the date's column-A label; a filled row is refused unless --force; every write is
read back from Drive and checked.
"""
from __future__ import annotations
import argparse, io, json, re, ssl, sys, urllib.parse, urllib.request, zipfile
from datetime import date, datetime, timedelta

import requests
from google.oauth2 import service_account
import google.auth.transport.requests as gtr

import config
from daily_sheet import WEEKDAY_TAB, COLUMN_OUTLET, row_label, _norm_daylabel
from dashboard_scrape import _RES_NAME

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

XLSX_ID = config.SALES_DATA_SHEET_ID   # the real .xlsx (1r9u4...)
PET_BASE = "https://billing.petpooja.com"
DRIVE = "https://www.googleapis.com/drive/v3/files/{id}"
DRIVE_UP = "https://www.googleapis.com/upload/drive/v3/files/{id}?uploadType=media&supportsAllDrives=true"
COLS = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U"]


def _num(s):
    try: return float(str(s).replace(",", "").strip())
    except Exception: return 0.0


def _pet(ep, d, cookie):
    body = urllib.parse.urlencode({"from_date": d, "to_date": d}).encode()
    rq = urllib.request.Request(PET_BASE + ep, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Requested-With": "XMLHttpRequest", "Cookie": cookie, "User-Agent": "Mozilla/5.0"})
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    return json.loads(urllib.request.urlopen(rq, timeout=45, context=ctx).read().decode())


def pull(d, cookie):
    rw = _pet("/users/load_restaurants_wise_data/", d, cookie)
    st = _pet("/users/load_sales_statistics/", d, cookie).get("Statistics_data") or {}
    by = {}
    for e in rw.get("all_restaurant_statistics", []):
        rid = e.get("res_id")
        if rid in (0, None): continue
        nm = _RES_NAME.get(int(rid))
        if nm: by[nm] = _num(e.get("total_sales"))
    ts = _num(st.get("total_sales")); net = _num(st.get("t_net"))
    online = _num(st.get("t_o")); disc = _num(st.get("total_discount"))
    z = _num(st.get("o_t_z")); orders = int(_num(st.get("total_orders")))
    B = [int(round(by.get(n, 0))) for _, n in COLUMN_OUTLET]
    errs = []
    if len(by) < 10: errs.append(f"only {len(by)}/10 outlets from Petpooja")
    if abs(sum(B) - ts) > 2: errs.append(f"outlet sum {sum(B):,.0f} != total {ts:,.0f}")
    if not net or not orders: errs.append("net or orders missing")
    if not online: errs.append("online missing")
    vals = {
        "B..K": B, "L": int(round(ts)), "N": int(round(net)), "R": orders,
        "O": round(net/ts, 10) if ts else 0, "P": round(disc/(net+disc), 4) if (net+disc) else 0,
        "Q": round(online/ts, 4) if ts else 0, "S": round((ts*0.95)/orders, 6) if orders else 0,
        "T": round(z/online, 4) if online else 0, "U": round(1 - z/online, 4) if online else 0,
    }
    return vals, errs


def creds_token():
    c = service_account.Credentials.from_service_account_file(
        str(config.SERVICE_ACCOUNT_FILE), scopes=["https://www.googleapis.com/auth/drive"])
    c.refresh(gtr.Request())
    return {"Authorization": f"Bearer {c.token}"}


def sheet_file_for_tab(zf, tab):
    """Return the xl/worksheets/sheetN.xml path backing the given tab name."""
    wb = zf.read("xl/workbook.xml").decode("utf-8")
    m = re.search(r'<sheet [^>]*name="%s"[^>]*r:id="(rId\d+)"' % re.escape(tab), wb)
    if not m: raise RuntimeError(f"tab {tab!r} not found in workbook.xml")
    rid = m.group(1)
    rels = zf.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    m2 = re.search(r'Id="%s"[^>]*Target="(worksheets/sheet\d+\.xml)"' % rid, rels)
    if not m2: raise RuntimeError(f"no target for {rid}")
    return "xl/" + m2.group(1)


def shared_strings(zf):
    try: s = zf.read("xl/sharedStrings.xml").decode("utf-8")
    except KeyError: return []
    return [''.join(re.findall(r'<t[^>]*>(.*?)</t>', si, re.S))
            for si in re.findall(r'<si>(.*?)</si>', s, re.S)]


def a_label(cell_xml, sst):
    """Resolve a column-A cell's displayed text (shared-string or inline)."""
    if 't="s"' in cell_xml:
        m = re.search(r'<v>(\d+)</v>', cell_xml)
        return sst[int(m.group(1))] if m and int(m.group(1)) < len(sst) else ""
    m = re.search(r'<v>(.*?)</v>', cell_xml, re.S)
    return m.group(1) if m else ""


def row_styles(sheet_xml, rn):
    """{col_letter: style_index} for row rn, or {} if absent."""
    m = re.search(r'<row r="%s"[ >].*?</row>' % rn, sheet_xml, re.S)
    if not m: return {}
    out = {}
    for c in re.finditer(r'<c r="([A-Z]+)%s"([^>]*?)(?:/>|>)' % rn, m.group(0)):
        s = re.search(r's="(\d+)"', c.group(2))
        out[c.group(1)] = s.group(1) if s else "0"
    return out


def build_row_xml(rn, vals, styles, a_cell_xml):
    def c(col, inner=""):
        s = styles.get(col, "0")
        return f'<c r="{col}{rn}" s="{s}">{inner}</c>' if inner else f'<c r="{col}{rn}" s="{s}"/>'
    parts = [re.sub(r'r="A\d+"', f'r="A{rn}"', a_cell_xml)]  # keep the existing date label cell
    outl = ["B","C","D","E","F","G","H","I","J","K"]
    for i, col in enumerate(outl):
        parts.append(c(col, f"<v>{vals['B..K'][i]}</v>"))
    parts.append(c("L", f"<f>SUM(B{rn}:K{rn})</f><v>{vals['L']}</v>"))
    parts.append(c("M"))
    parts.append(c("N", f"<v>{vals['N']}</v>"))
    parts.append(c("O", f"<f>N{rn}/L{rn}</f><v>{vals['O']}</v>"))
    parts.append(c("P", f"<v>{vals['P']}</v>"))
    parts.append(c("Q", f"<v>{vals['Q']}</v>"))
    parts.append(c("R", f"<v>{vals['R']}</v>"))
    parts.append(c("S", f"<f>(L{rn}*0.95)/R{rn}</f><v>{vals['S']}</v>"))
    parts.append(c("T", f"<v>{vals['T']}</v>"))
    parts.append(c("U", f"<f>1-T{rn}</f><v>{vals['U']}</v>"))
    for col in ["V","W","X","Y"]:
        parts.append(c(col))
    return f'<row r="{rn}" ht="14.25" customHeight="1">{"".join(parts)}</row>'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date"); ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    target = datetime.strptime(a.date, "%Y-%m-%d").date() if a.date else date.today() - timedelta(days=1)
    tab = WEEKDAY_TAB[target.weekday()]; want = _norm_daylabel(row_label(target))
    print(f"target : {target.isoformat()} ({target.strftime('%A')}) -> tab {tab}")

    cookie = json.load(open(config.SECRETS / "tokens.json"))["petpooja_cookie"]
    vals, errs = pull(target.isoformat(), cookie)
    if errs:
        print("SANITY FAILED — nothing written:"); [print("  -", e) for e in errs]; return 1
    print(f"pulled : L={vals['L']:,} N={vals['N']:,} orders={vals['R']} disc={vals['P']*100:.2f}%")

    H = creds_token()
    raw = requests.get(DRIVE.format(id=XLSX_ID) + "?alt=media&supportsAllDrives=true", headers=H, timeout=120).content
    zf = zipfile.ZipFile(io.BytesIO(raw))
    sheet_path = sheet_file_for_tab(zf, tab)
    sst = shared_strings(zf)
    sheet_xml = zf.read(sheet_path).decode("utf-8")

    # locate target row by column-A label
    target_rn = None
    for rm in re.finditer(r'<row r="(\d+)"[ >](.*?)</row>', sheet_xml, re.S):
        rn, body = rm.group(1), rm.group(2)
        acell = re.search(r'<c r="A%s"[^>]*?(?:/>|>.*?</c>)' % rn, body, re.S)
        if not acell: continue
        if _norm_daylabel(a_label(acell.group(0), sst)) == want:
            target_rn = int(rn); a_cell_xml = acell.group(0); break
    if target_rn is None:
        print(f"ABORT: no row carries the label for {row_label(target)!r} on tab {tab}. "
              "The month may not be seeded yet."); return 1
    print(f"row    : {target_rn}")

    # already filled?
    cur = re.search(r'<row r="%s"[ >].*?</row>' % target_rn, sheet_xml, re.S).group(0)
    filled = [c for c in re.findall(r'<c r="[B-K]%s"[^>]*>(?:<[^/].*?)</c>' % target_rn, cur)]
    has_data = bool(re.search(r'<c r="[B-K]%s"[^>]*><[fv]' % target_rn, cur))
    if has_data and not a.force:
        print(f"row {target_rn} already has data — refusing to overwrite (use --force). Done."); return 0

    # style template: prefer row target-2 (same banding parity), else target-1
    styles = row_styles(sheet_xml, target_rn - 2) or row_styles(sheet_xml, target_rn - 1) or row_styles(sheet_xml, target_rn)
    new_row = build_row_xml(target_rn, vals, styles, a_cell_xml)

    if a.dry_run:
        print("DRY-RUN — would write row:", new_row[:300], "..."); return 0

    sheet_xml2 = re.sub(r'<row r="%s"[ >].*?</row>' % target_rn, new_row, sheet_xml, count=1, flags=re.S)
    if sheet_xml2 == sheet_xml:
        print(f"row {target_rn} already matches the correct values — nothing to change. Done."); return 0

    # rebuild zip, only sheet_path changed
    out = io.BytesIO()
    zin = zipfile.ZipFile(io.BytesIO(raw))
    zout = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for item in zin.namelist():
        zout.writestr(item, sheet_xml2.encode("utf-8") if item == sheet_path else zin.read(item))
    zin.close(); zout.close()

    r = requests.patch(DRIVE_UP.format(id=XLSX_ID), headers={**H,
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        data=out.getvalue(), timeout=180)
    if r.status_code != 200:
        print("UPLOAD FAILED", r.status_code, r.text[:200]); return 1

    # verify by re-downloading and checking the row's B..K values in the sheet XML
    # (no openpyxl dependency — works with just the standard library + requests)
    v = requests.get(DRIVE.format(id=XLSX_ID) + "?alt=media&supportsAllDrives=true", headers=H, timeout=120).content
    vzf = zipfile.ZipFile(io.BytesIO(v))
    vsheet = vzf.read(sheet_path).decode("utf-8")
    vrow = re.search(r'<row r="%s"[ >].*?</row>' % target_rn, vsheet, re.S)
    ok = False
    if vrow:
        got = []
        for col in ["B","C","D","E","F","G","H","I","J","K"]:
            m = re.search(r'<c r="%s%s"[^>]*><v>([\d.]+)</v>' % (col, target_rn), vrow.group(0))
            got.append(int(round(float(m.group(1)))) if m else None)
        ok = got == vals["B..K"]
    nsheets = len(re.findall(r'<sheet ', vzf.read("xl/workbook.xml").decode("utf-8")))
    print(f"WROTE  : {tab}!row{target_rn}  outlets-verified={ok}  sheets={nsheets}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
