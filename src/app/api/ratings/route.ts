// Serves outlet ratings as JSON for the Ratings dashboard.
//
// Fetches reports/ratings.json from Supabase Storage (written daily by
// scripts/fetch-ratings.mjs). If the object is missing or unreachable, falls
// back to the bundled SAMPLE_RATINGS so the page always renders. The response
// is normalized to the RatingsData shape and carries a short cache window.
import { NextResponse } from 'next/server';
import { SAMPLE_RATINGS, type RatingsData } from '@/lib/ratings';

const RATINGS_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/ratings.json';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET() {
  let data: RatingsData = SAMPLE_RATINGS;

  try {
    const upstream = await fetch(RATINGS_URL, { cache: 'no-store' });
    if (upstream.ok) {
      const json = (await upstream.json()) as Partial<RatingsData>;
      if (json && Array.isArray(json.outlets) && json.outlets.length > 0) {
        data = {
          updatedAt: json.updatedAt ?? new Date().toISOString(),
          isSample: json.isSample ?? false,
          outlets: json.outlets,
        };
      }
    }
  } catch {
    // network/parse failure -> keep SAMPLE_RATINGS fallback
  }

  return NextResponse.json(data, {
    status: 200,
    headers: {
      'Cache-Control': 'public, max-age=300, stale-while-revalidate=900',
    },
  });
}
