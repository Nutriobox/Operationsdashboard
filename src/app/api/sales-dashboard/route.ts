// Proxies the latest sales dashboard report from Supabase Storage.
// Supabase serves all storage objects with a restrictive CSP `sandbox`
// directive that blocks JavaScript. We re-serve the same bytes from our own
// origin with the correct text/html content-type and no sandbox, so charts
// and other JS-driven dashboard interactions actually run.

import { NextResponse } from 'next/server';

const SUPABASE_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/sales-dashboard.html';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const upstream = await fetch(SUPABASE_URL, {
    // Pass through gzip so the body stays compressed on the wire.
    // Node will decompress automatically when we read it, but we'll
    // re-stream it as-is to keep the response small.
    headers: { 'Accept-Encoding': 'gzip' },
    cache: 'no-store',
  });

  if (!upstream.ok || !upstream.body) {
    return new NextResponse(`Failed to fetch report (status ${upstream.status})`, {
      status: 502,
    });
  }

  // Browsers will decompress transparently if we forward Content-Encoding.
  const headers = new Headers();
  headers.set('Content-Type', 'text/html; charset=utf-8');
  // Dashboard refreshes twice a day (9:30 AM + 4:40 PM IST). Keep cache short
  // so new uploads are visible within a minute. Allow stale-while-revalidate
  // for 1 hour to absorb traffic between refreshes.
  headers.set('Cache-Control', 'public, max-age=60, stale-while-revalidate=3600');
  const enc = upstream.headers.get('content-encoding');
  if (enc) headers.set('Content-Encoding', enc);
  // Forward Last-Modified / ETag so browsers + CDNs can revalidate cheaply.
  const lm = upstream.headers.get('last-modified');
  if (lm) headers.set('Last-Modified', lm);
  const et = upstream.headers.get('etag');
  if (et) headers.set('ETag', et);

  return new NextResponse(upstream.body, { status: 200, headers });
}
