"""
Weekly outlet-ratings refresh — Zomato / Swiggy / Google — driven by Playwright.

This is the Playwright port of the ratings task that previously ran through the
Claude-in-Chrome browser tools. It follows the same house pattern as
browser_export.py: one persistent Chromium profile (secrets/browser-profile,
the SAME profile refresh_tokens.py keeps signed in) drives real pages, and every
number is parsed off the DOM deterministically. The whole job — scrape all three
platforms for all 10 outlets, build ratings.json, append the weekly
ratings-history.json entry, upload both to Supabase, and verify the live API —
runs end to end in this one module.

Why a browser (not raw fetch): Google's per-business rating lives in the search
knowledge panel, and Swiggy's delivery pages are location-gated — neither is
reliably fetchable with a plain HTTP GET. Zomato exposes JSON-LD, which we read
straight from the rendered page.

Claude API is OFF the happy path. Parsing is deterministic. Only if a single
page's parser comes back empty do we fall back to claude_assist.extract_number()
to read the value off the page text — and only when ANTHROPIC_API_KEY is set
(automation/.env or the repo .env.local). If no key, that source simply keeps
its previous published value. A failed source NEVER overwrites good data with
null: the baseline ratings.json is the fallback for every field.

Usage:
    python ratings.py                # headless, scrape + upload + verify
    python ratings.py --headed       # watch the browser (debug)
    python ratings.py --dry-run      # scrape + build, print, DO NOT upload
    python ratings.py --selftest     # exercise build/history logic, no browser

Schedule weekly with Task Scheduler via run_ratings.bat (mirrors run_daily.bat).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config

try:
    import claude_assist
except Exception:  # noqa: BLE001 — assist is optional and must never block import
    claude_assist = None

PROFILE_DIR = config.SECRETS / "browser-profile"
IST = timezone(timedelta(hours=5, minutes=30))

RATINGS_JSON_OBJECT = "reports/ratings.json"
HISTORY_JSON_OBJECT = "reports/ratings-history.json"
PUBLIC_BASE = f"https://{config.SUPABASE_PROJECT}.supabase.co/storage/v1/object/public"
UPLOAD_BASE = f"https://{config.SUPABASE_PROJECT}.supabase.co/storage/v1/object"
API_RATINGS = f"{config.DASHBOARD_URL}/api/ratings"

SWIGGY_NOTE = ("Swiggy = Dineout rating for the 6 dine-in outlets; "
               "delivery rating (approx counts) for the 4 delivery-only outlets.")

# ---------------------------------------------------------------------------
# The 10 outlets, in the exact published order. `name`/`city` must match
# ratings.json byte-for-byte (the dashboard keys off them). swiggy_mode is
# "dineout" for the 6 dine-in outlets and "delivery" for the 4 delivery-only
# ones — this is the methodology note preserved in ratings.json.
# ---------------------------------------------------------------------------
OUTLETS = [
    {"name": "Rohini (Prashant Vihar)", "city": "Delhi",
     "google_q": "nutriobox prashant vihar rohini",
     "zomato": "https://www.zomato.com/ncr/nutriobox-prashant-vihar-new-delhi",
     "swiggy": "https://www.swiggy.com/restaurants/nutriobox-rohini-rohini-43183/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Janakpuri", "city": "Delhi",
     "google_q": "nutriobox janakpuri",
     "zomato": "https://www.zomato.com/ncr/nutriobox-janakpuri-new-delhi",
     "swiggy": "https://www.swiggy.com/restaurants/nutriobox-janakpuri-vikaspuri-delhi-228324/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Karkardooma", "city": "Delhi",
     "google_q": "nutriobox karkardooma preet vihar",
     "zomato": "https://www.zomato.com/ncr/nutriobox-karkardooma-new-delhi",
     "swiggy": "https://www.swiggy.com/restaurants/delhi/karkardooma/nutriobox-128137/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Dwarka (Sector 6)", "city": "Delhi",
     "google_q": "nutriobox dwarka sector 6",
     "zomato": "https://www.zomato.com/ncr/nutriobox-sector-6-dwarka-new-delhi",
     "swiggy": "https://www.swiggy.com/restaurants/nutriobox-dwarka-dwarka-453652/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Malviya Nagar (Shivalik)", "city": "Delhi",
     "google_q": "nutriobox malviya nagar shivalik",
     "zomato": "https://www.zomato.com/ncr/nutriobox-geetanjali-enclave-new-delhi",
     "swiggy": "https://www.swiggy.com/restaurants/delhi/geetanjali-enclave/nutriobox-450280/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Noida Sector 142", "city": "Noida",
     "google_q": "nutriobox noida sector 142 advant",
     "zomato": "https://www.zomato.com/ncr/nutriobox-sector-135-noida",
     "swiggy": "https://www.swiggy.com/restaurants/nutriobox-noida-expressway-noida-expressway-558627/dineout",
     "swiggy_mode": "dineout"},
    {"name": "Rajinder Nagar", "city": "Delhi",
     "google_q": "nutriobox rajinder nagar shankar road",
     "zomato": "https://www.zomato.com/ncr/nutriobox-rajinder-nagar-new-delhi",
     "swiggy": "https://www.swiggy.com/city/delhi/nutriobox-shankar-rd-karol-bagh-rest899925",
     "swiggy_mode": "delivery"},
    {"name": "Noida Sector 63", "city": "Noida",
     "google_q": "nutriobox noida sector 63",
     "zomato": "https://www.zomato.com/ncr/nutriobox-sector-63-noida",
     "swiggy": "https://www.swiggy.com/city/noida-1/nutriobox-gautam-buddha-nagar-sector-64-rest750998",
     "swiggy_mode": "delivery"},
    {"name": "Gurgaon DLF Phase 2", "city": "Gurugram",
     "google_q": "nutriobox dlf phase 2 gurgaon central arcade",
     "zomato": "https://www.zomato.com/ncr/nutriobox-dlf-phase-2-gurgaon",
     "swiggy": "https://www.swiggy.com/city/gurgaon/nutriobox-cyber-city-dlf-phase-2-rest979965",
     "swiggy_mode": "delivery"},
    {"name": "Gurgaon Sector 15", "city": "Gurugram",
     "google_q": "nutriobox sector 15 gurgaon",
     "zomato": "https://www.zomato.com/ncr/nutriobox-sector-15-gurgaon",
     "swiggy": "https://www.swiggy.com/city/gurgaon/nutriobox-sector-14-rest1056691",
     "swiggy_mode": "delivery"},
]


def log(*a) -> None:
    print(f"[ratings {datetime.now(timezone.utc).isoformat(timespec='seconds')}]", *a, flush=True)


# ---------------------------------------------------------------------------
# Page parsers (deterministic). Each returns {"rating": float, "reviews": int}
# or None. All three run in the page via page.evaluate.
# ---------------------------------------------------------------------------
_ZOMATO_JS = r"""
() => {
  const out = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
    try { const j = JSON.parse(s.textContent);
      (Array.isArray(j)?j:[j]).forEach(o => { if (o.aggregateRating) out.push({
        rv: o.aggregateRating.ratingValue,
        rc: o.aggregateRating.ratingCount || o.aggregateRating.reviewCount });
      });
    } catch(e){}
  });
  return out.length ? out[0] : null;
}
"""

_GOOGLE_JS = r"""
() => {
  let rating = null, reviews = null;
  const el = [...document.querySelectorAll('[aria-label]')]
    .find(e => /Rated\s+[\d.]+\s+out of 5/.test(e.getAttribute('aria-label')));
  if (el) { const m = el.getAttribute('aria-label').match(/Rated\s+([\d.]+)\s+out of 5/); if (m) rating = m[1]; }
  const bt = document.body.innerText;
  // Ratings and count sometimes render concatenated: "4.3517 Google reviews".
  const cm = bt.match(/(\d\.\d)([\d,]+)\s*Google reviews/);
  if (cm) { if (!rating) rating = cm[1]; reviews = cm[2].replace(/,/g,''); }
  else { const gm = bt.match(/([\d,]+)\s*Google reviews/); if (gm) reviews = gm[1].replace(/,/g,''); }
  return { rating, reviews };
}
"""

_SWIGGY_JS = r"""
() => {
  const bt = document.body.innerText;
  // "4.3 510 ratings" (dineout) or "4.6 (1.2K+ ratings)" (delivery)
  const m = bt.match(/(\d\.\d)\s*\(?\s*([\d.]+\s*K?\+?)\s*ratings/i);
  if (!m) return null;
  return { rating: m[1], count: m[2].trim() };
}
"""


def _num(x):
    """'4.3' -> 4.3, '' / None -> None."""
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _count(x):
    """'517' -> 517, '1.2K+' -> 1200, '' / None -> None."""
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    m = re.match(r"^([\d.]+)\s*([kK])?\+?$", s)
    if not m:
        return None
    val = float(m.group(1))
    if m.group(2):
        val *= 1000
    return int(round(val))


def _pair(rating, reviews):
    r, c = _num(rating), _count(reviews)
    if r is None and c is None:
        return None
    return {"rating": r, "reviews": c}


# These transient navigation states are races, not real failures: a page's own
# client-side redirect is still in flight when we issue the next goto. Retrying
# after a short settle clears them.
_RETRYABLE = ("interrupted by another navigation", "ERR_HTTP2_PROTOCOL_ERROR",
              "ERR_ABORTED", "ERR_NETWORK_CHANGED", "ERR_CONNECTION_RESET")


def _goto(page, url: str, tries: int = 3) -> None:
    """Navigate with a settle-and-retry on transient redirect/HTTP2 races.
    Also parks on about:blank first so a prior in-flight redirect can't bleed
    into and abort this navigation."""
    last = None
    for i in range(tries):
        try:
            try:
                page.goto("about:blank", wait_until="domcontentloaded", timeout=15_000)
            except Exception:
                pass
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            return
        except Exception as e:  # noqa: BLE001
            last = e
            if any(s in str(e) for s in _RETRYABLE) and i < tries - 1:
                page.wait_for_timeout(2000)
                continue
            raise
    if last:
        raise last


def google_via_api(query: str, api_key: str):
    """Google rating via the official Places API (New) Text Search — the
    reliable, ToS-clean path (search scraping gets a /sorry bot-check). Returns
    {'rating','reviews'} or None. Needs GOOGLE_PLACES_API_KEY in .env.local with
    the "Places API (New)" enabled on the Cloud project."""
    import urllib.request
    req = urllib.request.Request(
        "https://places.googleapis.com/v1/places:searchText",
        data=json.dumps({"textQuery": query, "regionCode": "IN"}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        res = (data.get("places") or [None])[0]
        if not res or res.get("rating") is None:
            return None
        return {"rating": float(res["rating"]), "reviews": res.get("userRatingCount")}
    except Exception as e:  # noqa: BLE001
        log(f"  places api failed for '{query}': {e}")
        return None


def _assist_source(text: str, what: str):
    """Optional Claude fallback when a deterministic parser found nothing."""
    if claude_assist is None or not claude_assist.available():
        return None
    res = claude_assist.extract_number(text, what)
    if res and res.ok and res.value is not None:
        log(f"  claude-assist recovered {what}: {res.value}")
        return res
    return None


# ---------------------------------------------------------------------------
# Scrape one outlet (all three platforms) on an already-open page.
# ---------------------------------------------------------------------------
def _scrape_zomato(page, o):
    try:
        _goto(page, o["zomato"])
        page.wait_for_timeout(1500)
        agg = page.evaluate(_ZOMATO_JS)
        if agg:
            return _pair(agg.get("rv"), agg.get("rc"))
        a = _assist_source(page.inner_text("body")[:8000], "Zomato rating value (0-5)")
        return _pair(a.value, None) if a else None
    except Exception as e:  # noqa: BLE001
        log(f"  zomato failed for {o['name']}: {e}")
        return None


def _scrape_google(page, o):
    try:
        _goto(page, "https://www.google.com/search?q=" + o["google_q"].replace(" ", "+"))
        page.wait_for_timeout(1200)
        if "/sorry/" in page.url or "/sorry" in page.url:
            log(f"  google served a bot-check (/sorry) for {o['name']} — run headed / sign in")
            return None
        r = page.evaluate(_GOOGLE_JS)
        pair = _pair(r.get("rating"), r.get("reviews")) if r else None
        if pair:
            return pair
        a = _assist_source(page.inner_text("body")[:8000],
                           "Google business star rating (0-5) from the knowledge panel")
        return _pair(a.value, None) if a else None
    except Exception as e:  # noqa: BLE001
        log(f"  google failed for {o['name']}: {e}")
        return None


def _scrape_swiggy(page, o):
    """Delivery city pages sometimes redirect home on first hit — reload once."""
    try:
        _goto(page, o["swiggy"])
        page.wait_for_timeout(2500)
        r = page.evaluate(_SWIGGY_JS)
        if not r and o["swiggy_mode"] == "delivery":
            _goto(page, o["swiggy"])
            page.wait_for_timeout(3500)
            r = page.evaluate(_SWIGGY_JS)
        if r:
            return _pair(r.get("rating"), r.get("count"))
        a = _assist_source(page.inner_text("body")[:8000], "Swiggy rating value (0-5)")
        return _pair(a.value, None) if a else None
    except Exception as e:  # noqa: BLE001
        log(f"  swiggy failed for {o['name']}: {e}")
        return None


def scrape_all(headless: bool = True, google_key: str | None = None) -> dict:
    """Return {outlet_name: {'zomato':..,'swiggy':..,'google':..}} — each a
    {'rating','reviews'} dict or None if that source failed this run.

    Google uses the Places API when google_key is set (reliable); otherwise it
    falls back to search scraping, which Google usually blocks with a /sorry
    bot-check — in which case that outlet's Google value keeps its baseline."""
    from playwright.sync_api import sync_playwright

    scraped: dict[str, dict] = {}
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=headless,
            args=["--disable-blink-features=AutomationControlled",
                  "--disable-features=IsolateOrigins,site-per-process"],
            viewport={"width": 1366, "height": 900},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        )
        # Hide the most obvious automation signal before any page script runs.
        try:
            ctx.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        except Exception:
            pass
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            for o in OUTLETS:
                log(f"scraping {o['name']}…")
                z = _scrape_zomato(page, o)
                g = (google_via_api(o["google_q"], google_key) if google_key
                     else _scrape_google(page, o))
                s = _scrape_swiggy(page, o)
                scraped[o["name"]] = {"zomato": z, "swiggy": s, "google": g}
                log(f"  zomato={z}  swiggy={s}  google={g}")
        finally:
            ctx.close()
    return scraped


# ---------------------------------------------------------------------------
# Build / history / upload (pure — unit-testable without a browser)
# ---------------------------------------------------------------------------
def _get_json(url: str):
    try:
        out = subprocess.run(["curl", "-sS", "-m", "60", "-H", "Cache-Control: no-cache", url],
                             capture_output=True, text=True).stdout
        return json.loads(out)
    except Exception:  # noqa: BLE001
        return None


def fetch_baseline():
    return _get_json(f"{PUBLIC_BASE}/{RATINGS_JSON_OBJECT}") or {"outlets": []}


def fetch_history():
    h = _get_json(f"{PUBLIC_BASE}/{HISTORY_JSON_OBJECT}")
    if not h or "weeks" not in h:
        return {"schema": "ratings-history-v1", "updatedAt": "",
                "note": "Weekly history of outlet ratings. Each entry = one ISO week. "
                        "aggregate = simple average across all outlets for that platform.",
                "weeks": []}
    return h


def build_ratings(scraped: dict, baseline: dict) -> dict:
    """A failed source keeps its baseline value — never writes null over good data."""
    base_by_name = {o.get("name"): o for o in baseline.get("outlets", [])}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    outlets = []
    for o in OUTLETS:
        s = scraped.get(o["name"], {})
        b = base_by_name.get(o["name"], {})
        entry = {"name": o["name"], "city": o["city"]}
        for plat in ("zomato", "swiggy", "google"):
            val = s.get(plat)
            if not val or val.get("rating") is None:
                val = b.get(plat) or {"rating": None, "reviews": None}
            entry[plat] = {"rating": val.get("rating"), "reviews": val.get("reviews")}
        outlets.append(entry)
    return {"updatedAt": now, "isSample": False, "swiggyNote": SWIGGY_NOTE, "outlets": outlets}


def update_history(ratings: dict, history: dict) -> tuple[dict, str]:
    """Replace this ISO week's entry in place, or append W<n+1>. weekStart =
    Monday (IST) of today; aggregate = simple mean of each platform's ratings."""
    outlets = ratings["outlets"]
    today = datetime.now(IST).date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    ws, we = week_start.isoformat(), week_end.isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    def agg(plat):
        vals = [o[plat]["rating"] for o in outlets if o[plat]["rating"] is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    aggregate = {"zomato": agg("zomato"), "swiggy": agg("swiggy"), "google": agg("google")}
    snapshot = [{"name": o["name"], "city": o["city"],
                 "zomato": o["zomato"], "swiggy": o["swiggy"], "google": o["google"]}
                for o in outlets]

    weeks = history["weeks"]
    existing = next((w for w in weeks if w.get("weekStart") == ws), None)
    if existing:
        existing.update({"weekEnd": we, "capturedAt": now,
                         "aggregate": aggregate, "outlets": snapshot})
        action = f"replaced {existing['week']}"
    else:
        label = f"W{len(weeks) + 1}"
        weeks.append({"week": label, "weekStart": ws, "weekEnd": we, "capturedAt": now,
                      "aggregate": aggregate, "outlets": snapshot})
        action = f"appended {label}"
    history["updatedAt"] = now
    return history, action


def upload_json(obj: dict, object_path: str, service_key: str) -> str:
    """Upsert a JSON object to Supabase Storage. Returns the HTTP code string."""
    tmp = config.ROOT / "outputs"
    tmp.mkdir(parents=True, exist_ok=True)
    fp = tmp / Path(object_path).name
    fp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    code = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-X", "POST", f"{UPLOAD_BASE}/{object_path}",
         "-H", f"apikey: {service_key}",
         "-H", f"Authorization: Bearer {service_key}",
         "-H", "Content-Type: application/json",
         "-H", "x-upsert: true",
         "--data-binary", f"@{fp}", "--max-time", "60"],
        capture_output=True, text=True,
    ).stdout.strip()
    return code


def verify_live() -> dict:
    d = _get_json(f"{API_RATINGS}?t={int(time.time())}") or {}
    return {"isSample": d.get("isSample"), "outlets": len(d.get("outlets", [])),
            "updatedAt": d.get("updatedAt")}


def _report(ratings: dict, scraped: dict) -> None:
    print("\n  Outlet                      Google        Zomato        Swiggy")
    print("  " + "-" * 66)
    for o in ratings["outlets"]:
        s = scraped.get(o["name"], {})
        def cell(plat):
            r = o[plat]["rating"]; c = o[plat]["reviews"]
            flag = "" if (s.get(plat) and s[plat].get("rating") is not None) else " (kept)"
            return f"{r}/{c}{flag}" if r is not None else "—"
        print(f"  {o['name'][:26]:<26}  {cell('google'):<13} {cell('zomato'):<13} {cell('swiggy')}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    headed = "--headed" in argv
    dry = "--dry-run" in argv
    selftest = "--selftest" in argv

    env = _read_env()
    svc = env.get("SUPABASE_SERVICE_ROLE_KEY")

    if selftest:
        # Exercise build + history with fixed data; no browser, no upload.
        fake = {o["name"]: {"zomato": {"rating": 4.4, "reviews": 100},
                            "swiggy": {"rating": 4.2, "reviews": 50},
                            "google": {"rating": 4.3, "reviews": 60}} for o in OUTLETS}
        ratings = build_ratings(fake, {"outlets": []})
        hist, action = update_history(ratings, fetch_history())
        assert len(ratings["outlets"]) == 10, "expected 10 outlets"
        log("selftest OK —", action, "| aggregate:", hist["weeks"][-1]["aggregate"])
        return 0

    if not svc:
        log("ERROR: SUPABASE_SERVICE_ROLE_KEY missing (.env.local)")
        return 1
    if claude_assist is not None:
        log("claude-assist:", "available (fallback armed)" if claude_assist.available()
            else "off (deterministic only)")

    google_key = env.get("GOOGLE_PLACES_API_KEY") or ""
    log("google source:", "Places API" if google_key
        else "search-scrape (may hit /sorry; baseline kept if so)")

    baseline = fetch_baseline()
    log(f"baseline has {len(baseline.get('outlets', []))} outlets")
    scraped = scrape_all(headless=not headed, google_key=google_key)

    ratings = build_ratings(scraped, baseline)
    failures = [f"{o['name']}/{p}" for o in OUTLETS
                for p in ("zomato", "swiggy", "google")
                if not (scraped.get(o["name"], {}).get(p) or {}).get("rating")]

    _report(ratings, scraped)
    if failures:
        log("sources that failed this run (baseline kept):", ", ".join(failures))
    else:
        log("all 30 sources captured — no baseline fallbacks needed")

    if dry:
        log("--dry-run: nothing uploaded")
        return 0

    c1 = upload_json(ratings, RATINGS_JSON_OBJECT, svc)
    log(f"upload ratings.json -> HTTP {c1}")
    if c1 != "200":
        log("ERROR: ratings.json upload failed; aborting before history")
        return 1

    history, action = update_history(ratings, fetch_history())
    c2 = upload_json(history, HISTORY_JSON_OBJECT, svc)
    log(f"upload ratings-history.json ({action}) -> HTTP {c2}")

    time.sleep(3)
    v = verify_live()
    log(f"live /api/ratings -> isSample={v['isSample']} outlets={v['outlets']} updatedAt={v['updatedAt']}")
    ok = c1 == "200" and c2 == "200" and v["isSample"] is False and v["outlets"] == 10
    log("DONE" if ok else "DONE WITH WARNINGS")
    return 0 if ok else 1


def _read_env() -> dict:
    try:
        from dashboard_build import read_env_local
        return read_env_local(config.ENV_LOCAL)
    except Exception:  # noqa: BLE001 — tolerate missing helper
        out = {}
        for line in Path(config.ENV_LOCAL).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
        return out


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
