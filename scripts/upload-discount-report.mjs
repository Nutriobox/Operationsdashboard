// Manually upload a Daily Offer Tracker report HTML file to Supabase Storage,
// bypassing the Gmail ingestion. Use this when the report needs to be pushed
// directly (e.g. the tracker email came from a different sender than the
// GitHub Action's `from:"NutrioBox Offer Tracker"` filter expects).
//
// Usage:
//   node scripts/upload-discount-report.mjs 2026-07-08 scripts/discount-codes-2026-07-08.html
//
// If the date is omitted it defaults to today's IST date; if the file is
// omitted it looks for scripts/discount-codes-<date>.html.
//
// Reads NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from the
// environment. When run locally, load them from .env.local first, e.g.:
//   node --env-file=.env.local scripts/upload-discount-report.mjs 2026-07-08

import { readFileSync } from 'node:fs';

const log = (m) => console.log(`[${new Date().toISOString()}] [upload] ${m}`);
const fail = (m) => { console.error(`[upload] [ERROR] ${m}`); process.exit(1); };

const { NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY } = process.env;
if (!NEXT_PUBLIC_SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  fail('Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. ' +
       'Run with:  node --env-file=.env.local scripts/upload-discount-report.mjs <date> [file]');
}

const istDate = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
}).format(new Date());

const date = process.argv[2] || istDate;
if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) fail(`Invalid date "${date}" (expected YYYY-MM-DD).`);

const file = process.argv[3] || `scripts/discount-codes-${date}.html`;
let html;
try { html = readFileSync(file, 'utf8'); }
catch (e) { fail(`Could not read HTML file "${file}": ${e.message}`); }

const objectName = `discount-codes-${date}.html`;
const url = `${NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/reports/${objectName}`;

log(`Uploading ${file} (${html.length} bytes) -> reports/${objectName} ...`);
const resp = await fetch(url, {
  method: 'PUT',
  headers: {
    Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
    apikey: SUPABASE_SERVICE_ROLE_KEY,
    'Content-Type': 'text/html; charset=utf-8',
    'x-upsert': 'true',
    'Cache-Control': 'public, max-age=60',
  },
  body: html,
});
if (!resp.ok) fail(`Upload failed (HTTP ${resp.status}): ${await resp.text()}`);
log(`Uploaded successfully.`);
log(`Live at: ${NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/reports/${objectName}`);
log(`Dashboard: https://operationsdashboard.nutriobox.com/dashboard/discount-codes  (pick ${date})`);
