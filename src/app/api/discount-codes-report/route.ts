// Proxies a date-specific discount codes report from Supabase Storage.
// Files are named `discount-codes-YYYY-MM-DD.html` and uploaded once per
// day from the "NutrioBox Daily Offer Tracker" email. We re-serve the bytes
// from our own origin with text/html headers so the iframe renders correctly
// (Supabase serves storage objects with a sandbox CSP and text/plain mime,
// both of which break in-browser rendering).
//
// Pass ?date=YYYY-MM-DD to fetch a specific day. If omitted, defaults to
// today's date in IST. If no report exists for that date, returns a small
// "no report available" HTML page (still 200, so the iframe renders it).
import { NextRequest, NextResponse } from 'next/server';

const BUCKET_BASE =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function todayInIst(): string {
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const now = new Date(Date.now() + IST_OFFSET_MS);
  return now.toISOString().slice(0, 10);
}

function isValidDate(s: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(s);
}

function notFoundHtml(date: string): string {
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>No report</title>
<style>
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       display:flex;align-items:center;justify-content:center;
       min-height:100vh;margin:0;background:#f8fafc;color:#475569;text-align:center;padding:24px}
  .card{max-width:480px}
  h1{margin:0 0 8px;font-size:22px;color:#0f172a}
  p{margin:6px 0;font-size:15px;line-height:1.5}
</style></head>
<body><div class="card">
  <h1>No discount report for ${date}</h1>
  <p>There's no NutrioBox Daily Offer Tracker email saved for this date yet.</p>
  <p>Reports are added automatically once the day's tracker email arrives.</p>
</div></body></html>`;
}

export async function GET(request: NextRequest) {
  const requested = request.nextUrl.searchParams.get('date') || todayInIst();
  const date = isValidDate(requested) ? requested : todayInIst();

  const url = `${BUCKET_BASE}/discount-codes-${date}.html`;
  const upstream = await fetch(url, { cache: 'no-store' });

  if (upstream.status === 404 || upstream.status === 400) {
    return new NextResponse(notFoundHtml(date), {
      status: 200,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store',
      },
    });
  }

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
