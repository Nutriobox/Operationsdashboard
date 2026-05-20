// Proxies the latest discount codes report from Supabase Storage.
// Same pattern as /api/sales-dashboard — re-serves the bytes from our origin
// with proper text/html headers, avoiding Supabase's sandbox CSP that would
// otherwise block any JS / styles inside the iframe.
import { NextResponse } from 'next/server';

const SUPABASE_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/discount-codes.html';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const upstream = await fetch(SUPABASE_URL, {
    headers: { 'Accept-Encoding': 'gzip' },
    cache: 'no-store',
  });

  if (!upstream.ok || !upstream.body) {
    return new NextResponse(`Failed to fetch report (status ${upstream.status})`, {
      status: 502,
    });
  }

  const headers = new Headers();
  headers.set('Content-Type', 'text/html; charset=utf-8');
  headers.set('Cache-Control', 'public, max-age=60, stale-while-revalidate=300');
  const enc = upstream.headers.get('content-encoding');
  if (enc) headers.set('Content-Encoding', enc);

  return new NextResponse(upstream.body, { status: 200, headers });
}
