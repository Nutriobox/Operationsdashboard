// Proxies the latest discount codes report from Supabase Storage.
// Re-serves the bytes from our own origin with text/html headers so the
// iframe renders correctly (Supabase serves storage objects with a sandbox
// CSP and text/plain mime, both of which break in-browser rendering).
import { NextResponse } from 'next/server';

const SUPABASE_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/discount-codes.html';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const upstream = await fetch(SUPABASE_URL, { cache: 'no-store' });

  if (!upstream.ok) {
    return new NextResponse(`Failed to fetch report (status ${upstream.status})`, {
      status: 502,
    });
  }

  const html = await upstream.text();

  return new NextResponse(html, {
    status: 200,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'public, max-age=60, stale-while-revalidate=300',
    },
  });
}
