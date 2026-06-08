// Shared types + bundled sample data for the Ratings dashboard.
//
// The live page fetches /api/ratings, which streams reports/ratings.json from
// Supabase Storage. Until the daily scraper (scripts/fetch-ratings.mjs) is
// wired up with real outlet URLs, the API falls back to SAMPLE_RATINGS below
// so the page always renders. Sample numbers are clearly placeholder — replace
// them by uploading a real ratings.json (see scripts/fetch-ratings.mjs).

export type PlatformKey = 'zomato' | 'swiggy' | 'google';

export type PlatformRating = {
  // Rating on the platform's own scale (all three use 0–5). null = no listing.
  rating: number | null;
  // Number of ratings/reviews backing it, if known.
  reviews: number | null;
};

export type OutletRating = {
  name: string;
  city: string;
  zomato: PlatformRating;
  swiggy: PlatformRating;
  google: PlatformRating;
};

export type RatingsData = {
  // ISO timestamp of when the data was last refreshed.
  updatedAt: string;
  // True when this is bundled placeholder data, not a real scrape.
  isSample: boolean;
  outlets: OutletRating[];
};

// Platform brand colors + labels, used across the dashboard UI.
export const PLATFORMS: { key: PlatformKey; label: string; color: string }[] = [
  { key: 'zomato', label: 'Zomato', color: '#E23744' },
  { key: 'swiggy', label: 'Swiggy', color: '#FC8019' },
  { key: 'google', label: 'Google', color: '#4285F4' },
];

// Placeholder data — replace with a real scrape. Outlet names are examples.
export const SAMPLE_RATINGS: RatingsData = {
  updatedAt: '2026-06-08T04:00:00.000Z',
  isSample: true,
  outlets: [
    {
      name: 'Koramangala',
      city: 'Bengaluru',
      zomato: { rating: 4.3, reviews: 1280 },
      swiggy: { rating: 4.2, reviews: 1015 },
      google: { rating: 4.5, reviews: 342 },
    },
    {
      name: 'Indiranagar',
      city: 'Bengaluru',
      zomato: { rating: 4.1, reviews: 980 },
      swiggy: { rating: 4.0, reviews: 870 },
      google: { rating: 4.4, reviews: 256 },
    },
    {
      name: 'HSR Layout',
      city: 'Bengaluru',
      zomato: { rating: 4.4, reviews: 1450 },
      swiggy: { rating: 4.3, reviews: 1190 },
      google: { rating: 4.6, reviews: 410 },
    },
    {
      name: 'Whitefield',
      city: 'Bengaluru',
      zomato: { rating: 3.9, reviews: 640 },
      swiggy: { rating: 4.1, reviews: 720 },
      google: { rating: 4.2, reviews: 188 },
    },
    {
      name: 'Jayanagar',
      city: 'Bengaluru',
      zomato: { rating: 4.2, reviews: 1100 },
      swiggy: { rating: 4.2, reviews: 960 },
      google: { rating: 4.5, reviews: 298 },
    },
    {
      name: 'Marathahalli',
      city: 'Bengaluru',
      zomato: { rating: 4.0, reviews: 760 },
      swiggy: { rating: 3.8, reviews: 540 },
      google: { rating: 4.3, reviews: 175 },
    },
  ],
};
