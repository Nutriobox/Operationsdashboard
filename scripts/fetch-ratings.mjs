// fetch-ratings.mjs — daily refresh of outlet ratings (Zomato / Swiggy / Google).
//
// Reads scripts/ratings-outlets.json (the per-outlet config), pulls the latest
// rating + review count from each platform, builds the RatingsData object, and
// uploads it to Supabase Storage as reports/ratings.json. The website's
// /api/ratings route serves that file to the Ratings dashboard.
//
// Run:  node scripts/fetch-ratings.mjs
// Schedule it once a day with Windows Task Scheduler, the same way as
// fetch-discount-email.ps1 (see the daily-checkin task file). A one-line
// wrapper .bat can simply `cd` to the repo and call this with node.
//
// --- DATA SOURCES & CAVEATS -------------------------------------------------
// Google  : Official Places API (legit, reliable). Needs GOOGLE_PLACES_API_KEY
//           in .env.local and a googlePlaceId per outlet. Returns `rating` and
//           `user_ratings_total` directly.
// Zomato  : No public API. We fetch the listing page and parse the embedded
//           JSON / aggregateRating. This is best-effort and WILL break whenever
//           Zomato changes their markup — failures fall back to the previous
//           value rather than crashing. Scraping may also violate their ToS;
//           confirm this is acceptable for your use before relying on it.
// Swiggy  : Same situation as Zomato — best-effort HTML parse, fragile.
//
// If a platform fetch fails for an outlet, that platform keeps the value from
// the existing reports/ratings.json (so one bad scrape doesn't wipe good data).
// ---------------------------------------------------------------------------

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ---- env -------------------------------------------------------------------
function loadEnv() {
  const env = {};
  try {
    const raw = readFileSync(join(ROOT, '.env.local'), 'utf8');
    for (const line of raw.split(/\r?\n/)) {
      const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
      if (m) env[m[1]] = m[2].replace(/^["']|["']$/g, '').trim();
    }
  } catch {
    /* ignore */
  }
  return env;
}
const ENV = loadEnv();
const SVC_KEY = ENV.SUPABASE_SERVICE_ROLE_KEY;
const GOOGLE_KEY = ENV.GOOGLE_PLACES_API_KEY || '';
const SUPABASE_BASE = 'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object';
const PUBLIC_URL = `${SUPABASE_BASE}/public/reports/ratings.json`;
const UPLOAD_URL = `${SUPABASE_BASE}/reports/ratings.json`;

const log = (...a) => console.log(`[ratings ${new Date().toISOString()}]`, ...a);

// ---- platform fetchers -----------------------------------------------------

async function fetchGoogle(placeId) {
  if (!placeId || !GOOGLE_KEY) return null;
  const url =
    `https://maps.googleapis.com/maps/api/place/details/json` +
    `?place_id=${encodeURIComponent(placeId)}&fields=rating,user_ratings_total&key=${GOOGLE_KEY}`;
  const r = await fetch(url);
  const j = await r.json();
  const res = j.result;
  if (!res || typeof res.rating !== 'number') return null;
  return { rating: res.rating, reviews: res.user_ratings_total ?? null };
}

// Best-effort: most food-delivery listing pages embed schema.org JSON-LD with
// an aggregateRating, or a JSON blob containing "ratingValue"/"aggregate".
function parseAggregateRating(html) {
  // 1) JSON-LD aggregateRating
  const ld = html.match(/"aggregateRating"\s*:\s*\{[^}]*\}/i);
  if (ld) {
    const val = ld[0].match(/"ratingValue"\s*:\s*"?([\d.]+)"?/i);
    const cnt = ld[0].match(/"(?:reviewCount|ratingCount)"\s*:\s*"?(\d+)"?/i);
    if (val) return { rating: parseFloat(val[1]), reviews: cnt ? parseInt(cnt[1], 10) : null };
  }
  // 2) Loose fallback: first ratingValue anywhere
  const loose = html.match(/"ratingValue"\s*:\s*"?([\d.]+)"?/i);
  if (loose) return { rating: parseFloat(loose[1]), reviews: null };
  return null;
}

async function fetchListing(url, label) {
  if (!url) return null;
  try {
    const r = await fetch(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',
        Accept: 'text/html',
      },
    });
    if (!r.ok) {
      log(`${label} HTTP ${r.status} for ${url}`);
      return null;
    }
    return parseAggregateRating(await r.text());
  } catch (e) {
    log(`${label} fetch failed:`, e.message);
    return null;
  }
}

// ---- main ------------------------------------------------------------------

async function main() {
  if (!SVC_KEY) {
    log('ERROR: SUPABASE_SERVICE_ROLE_KEY missing in .env.local');
    process.exit(1);
  }

  const cfg = JSON.parse(readFileSync(join(__dirname, 'ratings-outlets.json'), 'utf8'));

  // Pull existing data so we can preserve values when a fetch fails.
  let prev = { outlets: [] };
  try {
    const r = await fetch(PUBLIC_URL, { cache: 'no-store' });
    if (r.ok) prev = await r.json();
  } catch {
    /* first run — no previous file */
  }
  const prevByName = new Map((prev.outlets || []).map((o) => [o.name, o]));

  const outlets = [];
  for (const o of cfg.outlets) {
    const old = prevByName.get(o.name) || {};
    log(`Fetching ${o.name}…`);
    const [google, zomato, swiggy] = await Promise.all([
      fetchGoogle(o.googlePlaceId),
      fetchListing(o.zomatoUrl, 'zomato'),
      fetchListing(o.swiggyUrl, 'swiggy'),
    ]);
    outlets.push({
      name: o.name,
      city: o.city,
      zomato: zomato || old.zomato || { rating: null, reviews: null },
      swiggy: swiggy || old.swiggy || { rating: null, reviews: null },
      google: google || old.google || { rating: null, reviews: null },
    });
  }

  const payload = {
    updatedAt: new Date().toISOString(),
    isSample: false,
    outlets,
  };

  const up = await fetch(UPLOAD_URL, {
    method: 'POST',
    headers: {
      apikey: SVC_KEY,
      Authorization: `Bearer ${SVC_KEY}`,
      'Content-Type': 'application/json',
      'x-upsert': 'true',
    },
    body: JSON.stringify(payload),
  });
  if (!up.ok) {
    log('ERROR: upload failed', up.status, await up.text());
    process.exit(1);
  }
  log(`Uploaded ratings.json for ${outlets.length} outlets.`);
}

main().catch((e) => {
  log('FATAL', e);
  process.exit(1);
});
