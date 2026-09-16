// NutrioBox Operations Dashboard - automated daily health check + auto-fix.
//
// Replaces the Cowork/Claude-driven morning check. Runs standalone under
// Windows Task Scheduler. No Claude involvement.
//
//   Browser work  -> Playwright (site render check only)
//   Sheets tabs   -> Google Sheets API (no browser, no session expiry)
//   Storage       -> Supabase REST
//   Report        -> Gmail API (send)
//
// Usage:
//   node scripts/health-check.mjs            # full run
//   node scripts/health-check.mjs --dry-run  # detect only, never upload/send
//   node scripts/health-check.mjs --no-email # run fixes, print report, don't email
//
// Required in .env.local:
//   NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
//   GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
//   HEALTH_REPORT_TO           (optional, defaults to mayank@nutriobox.com)
//   NUTRIOBOX_REPORTS_DIR      (optional, defaults to C:\Users\hp\Downloads\NutrioBox_Reports)
//
// The refresh token must carry these scopes (run get-google-refresh-token.ps1):
//   gmail.readonly, gmail.send, spreadsheets.readonly

import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import crypto from 'node:crypto';
import dns from 'node:dns/promises';
import { fileURLToPath } from 'node:url';
import { Readable, pipeline } from 'node:stream';
import { promisify } from 'node:util';

const pipe = promisify(pipeline);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, '..');

const DRY_RUN = process.argv.includes('--dry-run');
const NO_EMAIL = process.argv.includes('--no-email');

// ---------------------------------------------------------------- constants
// Renamed 2026-08-22: operationsdashboard.* -> opsdashboard.* (Wix DNS + Vercel).
const SITE = 'https://opsdashboard.nutriobox.com';
const SITE_HOST = new URL(SITE).hostname;
const SALES_OBJECT = 'sales-dashboard.html';

const KOT = [
  {
    label: 'Daily KOT',
    sheetId: '1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8',
    pointer: 'kot-latest.json',
    cadence: 'daily',
  },
  {
    label: 'Weekly KOT',
    sheetId: '1eFBNV1bAwXqATegto9k0S2N9KfCGAtyufmbkpbzQX30',
    pointer: 'kot-weekly-latest.json',
    cadence: 'weekly',
  },
];

// ------------------------------------------------------------------ logging
const lines = [];
const stamp = () => new Date().toISOString();
const log = (m) => { console.log(`[${stamp()}] ${m}`); };
const report = (m) => { lines.push(m); console.log(`[${stamp()}] ${m}`); };

// --------------------------------------------------------------- env loader
function loadEnv() {
  const file = path.join(PROJECT_ROOT, '.env.local');
  if (!fs.existsSync(file)) throw new Error(`Missing .env.local at ${file}`);
  const out = {};
  for (const raw of fs.readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = raw.match(/^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*?)\s*$/);
    if (m) out[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
  // Real environment variables win, so a scheduled task or a test run can
  // override any single value without editing .env.local.
  return { ...out, ...Object.fromEntries(Object.entries(process.env).filter(([, v]) => v)) };
}

const env = loadEnv();
const SUPA_URL = env.NEXT_PUBLIC_SUPABASE_URL;
const SUPA_KEY = env.SUPABASE_SERVICE_ROLE_KEY;
// Reports go to the mailbox that owns the automation (mayank@), NOT satvik@.
const REPORT_TO = env.HEALTH_REPORT_TO || 'mayank@nutriobox.com';
const REPORTS_DIR = env.NUTRIOBOX_REPORTS_DIR || 'C:\\Users\\hp\\Downloads\\NutrioBox_Reports';

for (const k of ['NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY',
  'GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN']) {
  if (!env[k]) throw new Error(`Missing required env var ${k} in .env.local`);
}

const supaHeaders = {
  apikey: SUPA_KEY,
  Authorization: `Bearer ${SUPA_KEY}`,
};
const publicUrl = (name) => `${SUPA_URL}/storage/v1/object/public/reports/${name}`;
const objectUrl = (name) => `${SUPA_URL}/storage/v1/object/reports/${name}`;

// ------------------------------------------------------------- date helpers
const istParts = (d = new Date()) => {
  const f = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(d);
  const g = (t) => f.find((p) => p.type === t).value;
  return { y: +g('year'), m: +g('month'), d: +g('day') };
};
const istISODate = (d = new Date()) => {
  const { y, m, d: dd } = istParts(d);
  return `${y}-${String(m).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
};
const ordinal = (n) => {
  if (n % 100 >= 11 && n % 100 <= 13) return `${n}th`;
  return `${n}${['th', 'st', 'nd', 'rd'][n % 10] || 'th'}`;
};
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

/** "21st August" for the given IST date */
const tabNameDaily = (d) => {
  const { m, d: dd } = istParts(d);
  return `${ordinal(dd)} ${MONTHS[m - 1]}`;
};

/** Yesterday, in IST. */
function istYesterday() {
  return new Date(Date.now() - 24 * 3600 * 1000);
}

/** Monday..Sunday of the last COMPLETED week, in IST. */
function lastCompletedWeek() {
  const nowIst = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const dow = (nowIst.getDay() + 6) % 7;          // 0 = Monday
  const thisMonday = new Date(nowIst); thisMonday.setDate(nowIst.getDate() - dow);
  const monday = new Date(thisMonday); monday.setDate(thisMonday.getDate() - 7);
  const sunday = new Date(monday); sunday.setDate(monday.getDate() + 6);
  return { monday, sunday };
}
const tabNameWeekly = () => {
  const { monday, sunday } = lastCompletedWeek();
  const f = (x) => `${ordinal(x.getDate())} ${MONTHS[x.getMonth()]}`;
  return `${f(monday)} - ${f(sunday)}`;
};

// ------------------------------------------------------------ hash plumbing
/**
 * md5 of a stream that MAY be gzip-encoded. Node's fetch (undici) transparently
 * decompresses `content-encoding: gzip`, but a raw storage read might not be —
 * so sniff the gzip magic bytes on the first chunk and branch accordingly.
 */
function md5OfMaybeGzip(readable) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('md5');
    let decided = false;
    let sink = null;

    const finish = () => resolve(hash.digest('hex'));

    readable.on('error', reject);
    readable.on('data', (chunk) => {
      if (!decided) {
        decided = true;
        const isGzip = chunk.length >= 2 && chunk[0] === 0x1f && chunk[1] === 0x8b;
        if (isGzip) {
          sink = zlib.createGunzip();
          sink.on('data', (c) => hash.update(c));
          sink.on('error', reject);
          sink.on('end', finish);
        }
      }
      if (sink) sink.write(chunk);
      else hash.update(chunk);
    });
    readable.on('end', () => {
      if (sink) sink.end();
      else finish();
    });
  });
}

const md5File = (file) => md5OfMaybeGzip(fs.createReadStream(file));

// ------------------------------------------------------------ google oauth
let _token = null;
async function googleToken() {
  if (_token) return _token;
  const r = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: env.GMAIL_CLIENT_ID,
      client_secret: env.GMAIL_CLIENT_SECRET,
      refresh_token: env.GMAIL_REFRESH_TOKEN,
      grant_type: 'refresh_token',
    }),
  });
  if (!r.ok) {
    throw new Error(`Google token refresh failed (HTTP ${r.status}): ${await r.text()} ` +
      `- re-run scripts\\get-google-refresh-token.ps1`);
  }
  _token = (await r.json()).access_token;
  return _token;
}

/**
 * fetch with retry on transient failures. The Sheets API intermittently returns
 * 503 "service is currently unavailable" (seen 2026-08-22); without this a blip
 * would produce a false ❌ and, worse, tempt someone to ignore real ones.
 */
async function fetchRetry(url, opts = {}, tries = 3) {
  let last;
  for (let i = 0; i < tries; i++) {
    try {
      const r = await fetch(url, opts);
      if (r.ok || (r.status < 500 && r.status !== 429)) return r;
      last = new Error(`HTTP ${r.status}`);
    } catch (e) {
      last = e;
    }
    if (i < tries - 1) await new Promise((res) => setTimeout(res, 2000 * (i + 1)));
  }
  // Return the final attempt so callers can read the real status/body.
  return fetch(url, opts).catch(() => { throw last; });
}

// =====================================================================
// STEP 1 - Sales dashboard: compare content hashes, auto-upload on drift
// =====================================================================
async function checkSales() {
  const files = fs.existsSync(REPORTS_DIR)
    ? fs.readdirSync(REPORTS_DIR)
      .filter((f) => /^NutrioBox_Dashboard_.*\.html$/i.test(f))
      .map((f) => {
        const p = path.join(REPORTS_DIR, f);
        return { p, mtime: fs.statSync(p).mtime, size: fs.statSync(p).size };
      })
      .sort((a, b) => b.mtime - a.mtime)
    : [];

  if (files.length === 0) {
    report(`❌ Sales deploy - no NutrioBox_Dashboard_*.html found in ${REPORTS_DIR}. Check nutriobox-daily-data-v2.`);
    return;
  }

  const local = files[0];
  const localMd5 = await md5File(local.p);
  const freshToday = istISODate(local.mtime) === istISODate();
  log(`Local export: ${path.basename(local.p)} (${(local.size / 1e6).toFixed(1)} MB, md5 ${localMd5.slice(0, 8)}, mtime ${local.mtime.toISOString()})`);

  const liveResp = await fetch(publicUrl(SALES_OBJECT), { cache: 'no-store' });
  if (!liveResp.ok) {
    report(`❌ Sales deploy - Supabase object unreadable (HTTP ${liveResp.status}).`);
    return;
  }
  const liveMd5 = await md5OfMaybeGzip(Readable.fromWeb(liveResp.body));
  log(`Live object md5 ${liveMd5.slice(0, 8)}`);

  if (liveMd5 === localMd5) {
    report('✅ Sales deploy - content hash matches local export.');
    return;
  }

  if (!freshToday) {
    report(`❌ Sales deploy - live content differs from local export, but the local export is stale ` +
      `(last modified ${local.mtime.toISOString()}). NOT uploading. Check the nutriobox-daily-data-v2 export.`);
    return;
  }

  if (DRY_RUN) {
    report(`🔧 Sales deploy - hash mismatch, would upload (dry run).`);
    return;
  }

  // gzip -9 to a temp file, then POST with x-upsert
  const gz = path.join(PROJECT_ROOT, 'reports', `${SALES_OBJECT}.gz`);
  fs.mkdirSync(path.dirname(gz), { recursive: true });
  log('Compressing local export...');
  await pipe(
    fs.createReadStream(local.p),
    zlib.createGzip({ level: 9 }),
    fs.createWriteStream(gz),
  );
  const gzSize = fs.statSync(gz).size;
  if (gzSize > 50 * 1024 * 1024) {
    report(`❌ Sales deploy - gzipped export is ${(gzSize / 1e6).toFixed(1)} MB, over the 50 MB limit. Not uploading.`);
    return;
  }

  log(`Uploading ${(gzSize / 1e6).toFixed(1)} MB...`);
  const up = await fetch(objectUrl(SALES_OBJECT), {
    method: 'POST',
    headers: {
      ...supaHeaders,
      'Content-Type': 'text/html',
      'Content-Encoding': 'gzip',
      'Cache-Control': 'no-cache',
      'x-upsert': 'true',
    },
    body: fs.readFileSync(gz),
  });
  if (!up.ok) {
    report(`❌ Sales deploy - upload failed (HTTP ${up.status}): ${(await up.text()).slice(0, 200)}`);
    return;
  }

  // verify by content
  const verifyResp = await fetch(publicUrl(SALES_OBJECT), { cache: 'no-store' });
  const verifyMd5 = await md5OfMaybeGzip(Readable.fromWeb(verifyResp.body));
  const lastMod = verifyResp.headers.get('last-modified');
  fs.rmSync(gz, { force: true });

  if (verifyMd5 === localMd5) {
    report(`🔧 Sales deploy - live content was stale; re-uploaded ${path.basename(local.p)} ` +
      `(${(gzSize / 1e6).toFixed(1)} MB gz, last-modified ${lastMod}). Hash match confirmed. ` +
      `The 09:30 NutrioboxDailyDeploy likely failed or did not run.`);
  } else {
    report(`❌ Sales deploy - uploaded but verification hash still differs (live ${verifyMd5.slice(0, 8)} vs local ${localMd5.slice(0, 8)}).`);
  }
}

// =====================================================================
// STEP 2 - Discount codes: detect, fetch from Gmail only if a real email exists
// =====================================================================
async function checkDiscount() {
  const today = istISODate();
  const name = `discount-codes-${today}.html`;
  const head = await fetch(publicUrl(name), { method: 'HEAD', cache: 'no-store' });
  if (head.ok) {
    report(`✅ Discount fetch - ${name} present.`);
    return;
  }

  log(`Today's discount report missing; checking Gmail for a new Offer Tracker email...`);
  let token;
  try {
    token = await googleToken();
  } catch (e) {
    report(`❌ Discount fetch - ${name} missing and Gmail token refresh failed: ${e.message}`);
    return;
  }

  const q = 'from:"NutrioBox Offer Tracker" newer_than:1d';
  const listResp = await fetch(
    `https://gmail.googleapis.com/gmail/v1/users/me/messages?q=${encodeURIComponent(q)}&maxResults=10`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!listResp.ok) {
    report(`❌ Discount fetch - Gmail list failed (HTTP ${listResp.status}).`);
    return;
  }
  const list = await listResp.json();
  if (!list.messages?.length) {
    report(`❌ Discount fetch - ${name} missing and no Offer Tracker email in the last 24h. ` +
      `Upstream daily-offer-tracker task did not generate it.`);
    return;
  }

  if (DRY_RUN) {
    report('🔧 Discount fetch - a new email exists, would upload (dry run).');
    return;
  }

  const msgResp = await fetch(
    `https://gmail.googleapis.com/gmail/v1/users/me/messages/${list.messages[0].id}?format=full`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  const msg = await msgResp.json();
  const findHtml = (part) => {
    if (!part) return null;
    if (part.mimeType === 'text/html' && part.body?.data) return part.body.data;
    for (const p of part.parts || []) { const r = findHtml(p); if (r) return r; }
    return null;
  };
  const encoded = findHtml(msg.payload);
  if (!encoded) {
    report('❌ Discount fetch - Offer Tracker email found but it has no HTML body.');
    return;
  }
  const rawHtml = Buffer.from(encoded, 'base64url').toString('utf8');
  const pretty = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric',
  }).format(new Date());

  const wrapped = `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>NutrioBox Daily Offer Tracker - ${pretty}</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:1100px;margin:0 auto;padding:24px;color:#0f172a}
table{border-collapse:collapse;width:100%;font-size:14px}
td,th{border:1px solid #cbd5e1;padding:6px 10px}
th{background:#f1f5f9}
h1,h2,h3{color:#0f172a}
</style>
</head><body>
${rawHtml}
</body></html>`;

  const up = await fetch(objectUrl(name), {
    method: 'PUT',
    headers: {
      ...supaHeaders,
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=60',
      'x-upsert': 'true',
    },
    body: wrapped,
  });
  report(up.ok
    ? `🔧 Discount fetch - 05:00 job missed it; fetched today's Offer Tracker email and uploaded ${name}.`
    : `❌ Discount fetch - upload of ${name} failed (HTTP ${up.status}).`);
}

// =====================================================================
// STEP 3 - KOT pointers: read newest tab via Sheets API, self-heal the JSON
// =====================================================================
async function checkKotPointers() {
  let token;
  try {
    token = await googleToken();
  } catch (e) {
    report(`❌ KOT pointers - Google token refresh failed: ${e.message}`);
    return {};
  }

  const resolved = {};

  for (const cfg of KOT) {
    try {
      // Newest tab is the LEFTMOST tab => properties.index === 0
      const metaResp = await fetchRetry(
        `https://sheets.googleapis.com/v4/spreadsheets/${cfg.sheetId}` +
        `?fields=sheets(properties(sheetId,title,index))`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (!metaResp.ok) {
        const raw = await metaResp.text();
        let why = raw.slice(0, 150);
        try { why = JSON.parse(raw).error?.message || why; } catch { /* keep raw */ }
        const hint = metaResp.status === 403
          ? ' Re-run scripts\\get-google-refresh-token.ps1 to grant spreadsheets.readonly (and enable the Sheets API in Cloud Console).'
          : metaResp.status === 404
            ? ' Check the sheet ID and that mayank@nutriobox.com can view it.'
            : '';
        report(`❌ ${cfg.label} pointer - Sheets API read failed (HTTP ${metaResp.status}): ${why}${hint}`);
        continue;
      }
      const meta = await metaResp.json();
      const newest = meta.sheets
        .map((s) => s.properties)
        .sort((a, b) => a.index - b.index)[0];
      const newestGid = String(newest.sheetId);
      const newestName = newest.title.trim();

      const expected = cfg.cadence === 'daily' ? tabNameDaily(istYesterday()) : tabNameWeekly();
      const coversDate = cfg.cadence === 'daily'
        ? istISODate(istYesterday())
        : istISODate(lastCompletedWeek().monday);

      const ptrResp = await fetch(`${publicUrl(cfg.pointer)}?t=${Date.now()}`, { cache: 'no-store' });
      const ptr = ptrResp.ok ? await ptrResp.json().catch(() => ({})) : {};
      resolved[cfg.pointer] = newestGid;

      const stale = String(ptr.gid || '') !== newestGid;
      const behind = newestName !== expected;

      if (!stale) {
        report(`✅ ${cfg.label} pointer - already on "${newestName}".` +
          (behind ? ` ⚠️ but expected "${expected}" - the tab-creating task did not run.` : ''));
      } else if (DRY_RUN) {
        report(`🔧 ${cfg.label} pointer - would repoint ${ptr.gid || 'none'} -> ${newestGid} ("${newestName}") (dry run).`);
      } else {
        const payload = JSON.stringify({
          sheetId: cfg.sheetId,
          gid: newestGid,
          tabName: newestName,
          date: coversDate,
          updatedAt: new Date().toISOString(),
        });
        const up = await fetch(objectUrl(cfg.pointer), {
          method: 'PUT',
          headers: {
            ...supaHeaders,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, max-age=60',
            'x-upsert': 'true',
          },
          body: payload,
        });
        report(up.ok
          ? `🔧 ${cfg.label} pointer - was stuck on "${ptr.tabName || '?'}" (gid ${ptr.gid || 'none'}); ` +
            `repointed to "${newestName}" (gid ${newestGid}).` +
            (behind ? ` ⚠️ expected "${expected}" - tab-creating task did not run.` : '')
          : `❌ ${cfg.label} pointer - republish failed (HTTP ${up.status}).`);
      }

      if (behind) {
        report(`   ↳ Newest tab in the sheet is "${newestName}", expected "${expected}".`);
      }
    } catch (e) {
      report(`❌ ${cfg.label} pointer - ${e.message}`);
    }
  }

  return resolved;
}

// =====================================================================
// STEP 4 - Playwright render check
// =====================================================================
async function checkRender(expectedGids) {
  // Fail fast and clearly on DNS, which is a different problem from a bad build.
  try {
    await dns.lookup(SITE_HOST);
  } catch {
    report(`❌ Site render - ${SITE_HOST} does not resolve. ` +
      `Check the CNAME for "${SITE_HOST.split('.')[0]}" in Wix DNS and the domain in Vercel.`);
    return;
  }

  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    report('❌ Site render - Playwright is not installed. Run: npm i -D playwright && npx playwright install chromium');
    return;
  }

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const consoleErrors = [];
    page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });

    const resp = await page.goto(SITE, { waitUntil: 'domcontentloaded', timeout: 45000 });
    const status = resp?.status() ?? 0;
    if (status >= 400) {
      report(`❌ Site render - ${SITE} returned HTTP ${status}.`);
      return;
    }

    // Deliberately NOT touching the Sales Item card: it embeds ~100 MB of HTML
    // and will hang the renderer. Sales health is proven by the hash check.
    await page.waitForTimeout(2500);
    const text = (await page.innerText('body').catch(() => '')).slice(0, 4000);
    const loginWall = /sign in|log in|password|email/i.test(text) && !/dashboard/i.test(text);

    if (loginWall) {
      report(`✅ Site render - reachable (HTTP ${status}); login page rendered as expected.`);
    } else if (text.trim().length < 40) {
      report(`❌ Site render - page loaded (HTTP ${status}) but the body is essentially empty.`);
    } else {
      report(`✅ Site render - dashboard rendered (HTTP ${status}).`);
    }

    // If we got past auth, confirm the KOT buttons resolve to the repaired gids.
    const hrefs = await page.$$eval('a[href*="docs.google.com"]', (as) => as.map((a) => a.href))
      .catch(() => []);
    if (hrefs.length && Object.keys(expectedGids || {}).length) {
      for (const [pointer, gid] of Object.entries(expectedGids)) {
        const sheetId = KOT.find((k) => k.pointer === pointer).sheetId;
        const link = hrefs.find((h) => h.includes(sheetId));
        if (link && !link.includes(`gid=${gid}`)) {
          report(`❌ ${pointer} - dashboard link still points elsewhere: ${link}`);
        }
      }
    }

    if (consoleErrors.length) {
      log(`Console errors: ${consoleErrors.slice(0, 3).join(' | ')}`);
    }
  } catch (e) {
    report(`❌ Site render - ${e.message.split('\n')[0]}`);
  } finally {
    await browser.close();
  }
}

// =====================================================================
// STEP 5 - Email the report
// =====================================================================
async function sendReport() {
  const today = istISODate();
  const bad = lines.filter((l) => l.startsWith('❌')).length;
  const fixed = lines.filter((l) => l.startsWith('🔧')).length;
  const subject = bad
    ? `[NutrioBox] Dashboard health check - ${bad} issue${bad > 1 ? 's' : ''} - ${today}`
    : fixed
      ? `[NutrioBox] Dashboard health check - ${fixed} auto-fixed - ${today}`
      : `[NutrioBox] Dashboard health check - all green - ${today}`;

  const body = `${lines.join('\n')}\n\n--\nAutomated by scripts/health-check.mjs on ${new Date().toString()}\n`;

  if (NO_EMAIL || DRY_RUN) {
    log(`(email suppressed) would send To: ${REPORT_TO}\nSubject: ${subject}\n\n${body}`);
    return;
  }

  const token = await googleToken();
  const mime = [
    `To: ${REPORT_TO}`,
    `Subject: ${subject}`,
    'Content-Type: text/plain; charset=utf-8',
    '',
    body,
  ].join('\r\n');

  const r = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw: Buffer.from(mime).toString('base64url') }),
  });
  if (!r.ok) {
    console.error(`Failed to send report email (HTTP ${r.status}): ${(await r.text()).slice(0, 300)}`);
    console.error('If this is a scope error, re-run scripts\\get-google-refresh-token.ps1 to add gmail.send.');
  } else {
    log(`Report emailed to ${REPORT_TO}.`);
  }
}

// ==================================================================== main
async function main() {
  log(`NutrioBox dashboard health check - ${istISODate()} IST${DRY_RUN ? ' (DRY RUN)' : ''}`);

  await checkSales().catch((e) => report(`❌ Sales deploy - ${e.message}`));
  await checkDiscount().catch((e) => report(`❌ Discount fetch - ${e.message}`));
  const gids = await checkKotPointers().catch((e) => { report(`❌ KOT pointers - ${e.message}`); return {}; });
  await checkRender(gids).catch((e) => report(`❌ Site render - ${e.message}`));

  console.log('\n===== REPORT =====\n' + lines.join('\n') + '\n==================\n');
  await sendReport().catch((e) => console.error(`Report send failed: ${e.message}`));

  process.exit(lines.some((l) => l.startsWith('❌')) ? 1 : 0);
}

main().catch((e) => { console.error(e?.stack || String(e)); process.exit(1); });
