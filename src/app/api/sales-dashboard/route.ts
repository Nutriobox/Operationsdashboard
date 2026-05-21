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
  // Report updates once daily at 5:30 AM IST. Cache aggressively:
  // 4 hours fresh + serve stale for 12 hours while revalidating in background.
  headers.set('Cache-Control', 'public, max-age=14400, stale-while-revalidate=43200');
  const enc = upstream.headers.get('content-encoding');
  if (enc) headers.set('Content-Encoding', enc);

  return new NextResponse(upstream.body, { status: 200, headers });
}
