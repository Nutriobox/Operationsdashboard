// Returns the latest available discount codes report date.
// Lists files in the Supabase Storage "reports" bucket that match the
// `discount-codes-YYYY-MM-DD.html` naming scheme, sorts descending, and
// returns the most recent date so the discount codes page can default
// the picker to "latest available" rather than today.
//
// Also returns the full list of available dates so the UI could later
// disable empty days in the calendar if we wanted that.
import { NextResponse } from 'next/server';

const SUPABASE_URL = 'https://jkzremlkrxhhshqouudk.supabase.co';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  const secretKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!secretKey) {
    return NextResponse.json(
      { latestDate: null, error: 'missing-service-role-key' },
      { status: 500 }
    );
  }

  const r = await fetch(`${SUPABASE_URL}/storage/v1/object/list/reports`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${secretKey}`,
      apikey: secretKey,
      'Content-Type': 'application/json',
    },
    // NB: Supabase's `prefix` is a folder path, not a substring filter.
    // The reports bucket is flat, so we ask for all files at the root and
    // filter to discount-codes-YYYY-MM-DD.html in code below.
    body: JSON.stringify({
      prefix: '',
      limit: 1000,
      sortBy: { column: 'name', order: 'desc' },
    }),
    cache: 'no-store',
  });

  if (!r.ok) {
    return NextResponse.json(
      { latestDate: null, error: `supabase-${r.status}` },
      { status: 502 }
    );
  }

  const items: Array<{ name?: string }> = await r.json();
  const dates = items
    .map((i) => (i.name || '').match(/^discount-codes-(\d{4}-\d{2}-\d{2})\.html$/))
    .filter((m): m is RegExpMatchArray => !!m)
    .map((m) => m[1])
    .sort()
    .reverse();

  return NextResponse.json(
    { latestDate: dates[0] || null, dates },
    { headers: { 'Cache-Control': 'no-store' } }
  );
}
