// Proxies the weekly ratings history (reports/ratings-history.json) from
// Supabase Storage and re-serves it same-origin as application/json. This is
// what the Ratings trend line chart reads to plot week-over-week. The weekly
// refresh task appends one entry per ISO week to this object.
import { NextResponse } from 'next/server';

const SUPABASE_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/ratings-history.json';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const upstream = await fetch(SUPABASE_URL, { cache: 'no-store' });

  if (!upstream.ok) {
    return new NextResponse(`Failed to fetch ratings history (status ${upstream.status})`, {
      status: 502,
    });
  }

  const body = await upstream.text();

  return new NextResponse(body, {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=60, stale-while-revalidate=300',
    },
  });
}
