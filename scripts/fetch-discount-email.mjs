// Cloud version of fetch-discount-email.ps1 — runs in GitHub Actions (Node 22),
// so the 05:00 IST discount fetch no longer depends on the laptop being awake.
//
// Reads all secrets from environment variables (set as GitHub Actions secrets):
//   GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN,
//   NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
//
// Steps mirror the PowerShell version exactly:
//   1. Exchange the refresh token for a short-lived access token.
//   2. Query Gmail for today's "NutrioBox Offer Tracker" email.
//   3. Extract the text/html body and decode it.
//   4. Wrap with the same styling as the in-browser scrape.
//   5. PUT it to Supabase Storage as discount-codes-YYYY-MM-DD.html (IST date).

const log = (msg) => console.log(`[${new Date().toISOString()}] [discount] ${msg}`);
const fail = (msg) => { console.error(`[${new Date().toISOString()}] [discount] [ERROR] ${msg}`); process.exit(1); };

const {
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN,
  NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
} = process.env;

for (const [k, v] of Object.entries({
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN,
  NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY,
})) {
  if (!v) fail(`Missing required env var ${k}`);
}

// Dates computed in IST (Asia/Kolkata), matching the original report timestamps.
const istDate = new Intl.DateTimeFormat('en-CA', {
  timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
}).format(new Date()); // -> "2026-06-04"
const prettyDate = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric',
}).format(new Date()); // -> "04 Jun 2026"

async function main() {
  log(`Looking for today's report (${istDate})...`);

  // 1. Refresh access token
  log('Refreshing access token...');
  const tokenResp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: GMAIL_CLIENT_ID,
      client_secret: GMAIL_CLIENT_SECRET,
      refresh_token: GMAIL_REFRESH_TOKEN,
      grant_type: 'refresh_token',
    }),
  });
  if (!tokenResp.ok) {
    fail(`Token refresh failed (HTTP ${tokenResp.status}): ${await tokenResp.text()}. ` +
         `The Gmail refresh token may have been revoked — re-auth and update the GMAIL_REFRESH_TOKEN secret.`);
  }
  const accessToken = (await tokenResp.json()).access_token;
  log('Got access token.');

  const authHeaders = { Authorization: `Bearer ${accessToken}` };

  // 2. List today's tracker emails
  const query = 'from:"NutrioBox Offer Tracker" newer_than:1d';
  const listUrl = `https://gmail.googleapis.com/gmail/v1/users/me/messages?q=${encodeURIComponent(query)}&maxResults=10`;
  const listResp = await fetch(listUrl, { headers: authHeaders });
  if (!listResp.ok) fail(`Gmail list failed (HTTP ${listResp.status}): ${await listResp.text()}`);
  const list = await listResp.json();

  if (!list.messages || list.messages.length === 0) {
    log('No NutrioBox Offer Tracker emails in the last 24 hours. Nothing to upload.');
    return; // soft success
  }
  log(`Found ${list.messages.length} candidate message(s). Using the most recent.`);

  // 3. Fetch the newest message (Gmail returns newest first)
  const msgUrl = `https://gmail.googleapis.com/gmail/v1/users/me/messages/${list.messages[0].id}?format=full`;
  const msgResp = await fetch(msgUrl, { headers: authHeaders });
  if (!msgResp.ok) fail(`Failed to fetch message (HTTP ${msgResp.status}): ${await msgResp.text()}`);
  const msg = await msgResp.json();

  // 4. Recursively find the text/html part
  const findHtml = (part) => {
    if (!part) return null;
    if (part.mimeType === 'text/html' && part.body?.data) return part.body.data;
    if (part.parts) {
      for (const p of part.parts) {
        const r = findHtml(p);
        if (r) return r;
      }
    }
    return null;
  };
  const encodedHtml = findHtml(msg.payload);
  if (!encodedHtml) fail('No HTML body found in message.');

  // Gmail returns base64url
  const rawHtml = Buffer.from(encodedHtml, 'base64url').toString('utf8');
  log(`Extracted HTML body: ${rawHtml.length} chars.`);

  // 5. Wrap with the same styling as the in-browser scrape
  const wrappedHtml = `<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>NutrioBox Daily Offer Tracker - ${prettyDate}</title>
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

  // 6. Upload to Supabase Storage
  const objectName = `discount-codes-${istDate}.html`;
  const uploadUrl = `${NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/reports/${objectName}`;
  log(`Uploading to ${uploadUrl} ...`);
  const upResp = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      apikey: SUPABASE_SERVICE_ROLE_KEY,
      'Content-Type': 'text/html; charset=utf-8',
      'x-upsert': 'true',
      'Cache-Control': 'public, max-age=60',
    },
    body: wrappedHtml,
  });
  if (!upResp.ok) fail(`Upload failed (HTTP ${upResp.status}): ${await upResp.text()}`);
  log(`Uploaded ${objectName} successfully.`);
  log(`Public URL: ${NEXT_PUBLIC_SUPABASE_URL}/storage/v1/object/public/reports/${objectName}`);
}

main().catch((e) => fail(e?.stack || String(e)));
