// Proxies the latest sales dashboard report from Supabase Storage.
// Supabase serves all storage objects with a restrictive CSP `sandbox`
// directive that blocks JavaScript. We re-serve the same bytes from our own
// origin with the correct text/html content-type and no sandbox, so charts
// and other JS-driven dashboard interactions actually run.
//
// 2026-10-21 fix: the previous version set Accept-Encoding: gzip and forwarded
// upstream.body "as-is", assuming it stayed compressed. In Vercel's Node
// runtime the fetch body is DECOMPRESSED (~37 MB), and a Node serverless
// function response is capped at ~4.5 MB — so it returned an EMPTY 200 and the
// dashboard hung forever on "the report is rendering". We now read the HTML and
// re-gzip it ourselves, so the response body is the compressed ~4 MB (well
// under the cap) and the browser decompresses it transparently. This depends on
// the report staying small (see automation/shrink_dashboard.py, which keeps the
// file to ~4 MB gzip); if it ever grows past the cap again, switch this route
// to `export const runtime = 'edge'` (Edge streams without the 4.5 MB cap).

import { NextResponse } from 'next/server';
import { gzipSync } from 'zlib';

const SUPABASE_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/sales-dashboard.html';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const upstream = await fetch(SUPABASE_URL, { cache: 'no-store' });

  if (!upstream.ok) {
    return new NextResponse(`Failed to fetch report (status ${upstream.status})`, {
      status: 502,
    });
  }

  // upstream is auto-decompressed to full HTML text here.
  const html = await upstream.text();
  // Re-compress ourselves so the response body stays well under Vercel's
  // ~4.5 MB serverless response cap. Max level for the most headroom; this
  // runs at most once per minute thanks to the Cache-Control below.
  const body = gzipSync(html, { level: 9 });

  const headers = new Headers();
  headers.set('Content-Type', 'text/html; charset=utf-8');
  headers.set('Content-Encoding', 'gzip');
  // Dashboard refreshes twice a day (9:30 AM + 4:40 PM IST). Keep cache short
  // so new uploads are visible within a minute. Allow stale-while-revalidate
  // for 1 hour to absorb traffic between refreshes.
  headers.set('Cache-Control', 'public, max-age=60, stale-while-revalidate=3600');
  const lm = upstream.headers.get('last-modified');
  if (lm) headers.set('Last-Modified', lm);
  const et = upstream.headers.get('etag');
  if (et) headers.set('ETag', et);

  return new NextResponse(body, { status: 200, headers });
}
