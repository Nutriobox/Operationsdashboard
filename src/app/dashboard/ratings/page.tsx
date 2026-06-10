// Ratings Dashboard — a modern, Power-BI-style view of each outlet's
// Zomato, Swiggy and Google ratings.
//
// Data comes from /api/ratings (reports/ratings.json on Supabase, refreshed
// daily by scripts/fetch-ratings.mjs; falls back to bundled sample data).
// Everything here is rendered natively (Recharts + Tailwind) so the look is
// fully controlled — no iframe.
'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { PLATFORMS, type PlatformKey, type RatingsData, type OutletRating } from '@/lib/ratings';

// Weekly history powers the trend line chart. Shape matches
// reports/ratings-history.json, surfaced same-origin via /api/ratings-history.
type WeeklyAggregate = { zomato: number | null; swiggy: number | null; google: number | null };
type WeekEntry = { week: string; weekStart: string; weekEnd: string; capturedAt?: string; aggregate: WeeklyAggregate; outlets: OutletRating[] };
type RatingsHistory = { weeks: WeekEntry[] };

const HISTORY_URLS = [
  '/api/ratings-history',
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/ratings-history.json',
];

function isoMondayOf(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  const off = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - off);
  return d.toISOString().slice(0, 10);
}

function avg(nums: number[]): number | null {
  const v = nums.filter((n) => typeof n === 'number' && !Number.isNaN(n));
  if (v.length === 0) return null;
  return v.reduce((a, b) => a + b, 0) / v.length;
}

function fmt(n: number | null, digits = 1): string {
  return n == null ? '—' : n.toFixed(digits);
}

function fmtInt(n: number | null): string {
  return n == null ? '—' : n.toLocaleString('en-IN');
}

function relativeUpdated(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata',
  });
}

// Five stars for a 0–5 value, with a partial-fill last star.
function Stars({ value, color }: { value: number | null; color: string }) {
  const v = value ?? 0;
  return (
    <div className="flex items-center gap-0.5" aria-label={`${fmt(value)} out of 5`}>
      {[0, 1, 2, 3, 4].map((i) => {
        const fill = Math.max(0, Math.min(1, v - i)); // 0..1 for this star
        return (
          <span key={i} className="relative inline-block h-4 w-4">
            <svg viewBox="0 0 20 20" className="absolute inset-0 h-4 w-4 text-slate-200" fill="currentColor">
              <path d="M10 1.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L10 15l-5.2 2.6 1-5.8L1.5 7.7l5.9-.9L10 1.5z" />
            </svg>
            <span className="absolute inset-0 overflow-hidden" style={{ width: `${fill * 100}%` }}>
              <svg viewBox="0 0 20 20" className="h-4 w-4" fill={color}>
                <path d="M10 1.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L10 15l-5.2 2.6 1-5.8L1.5 7.7l5.9-.9L10 1.5z" />
              </svg>
            </span>
          </span>
        );
      })}
    </div>
  );
}

function platformMeta(key: PlatformKey) {
  return PLATFORMS.find((p) => p.key === key)!;
}

export default function RatingsPage() {
  const [data, setData] = useState<RatingsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [sortBy, setSortBy] = useState<'overall' | PlatformKey>('overall');

  const load = () => {
    setLoading(true);
    setError(false);
    fetch('/api/ratings', { cache: 'no-store' })
      .then((r) => r.json())
      .then((j: RatingsData) => setData(j))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  // Weekly history for the trend chart + calendar week picker.
  const [history, setHistory] = useState<RatingsHistory | null>(null);
  const [weekIdx, setWeekIdx] = useState<number>(-1); // -1 = latest week

  useEffect(() => {
    let cancelled = false;
    (async () => {
      for (const u of HISTORY_URLS) {
        try {
          const r = await fetch(u, { cache: 'no-store' });
          if (!r.ok) continue;
          const j = (await r.json()) as RatingsHistory;
          if (!cancelled && j && Array.isArray(j.weeks) && j.weeks.length) {
            setHistory(j);
            return;
          }
        } catch {
          // try the next source
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const weeks = history?.weeks ?? [];
  const curWeek = weeks.length ? (weekIdx < 0 ? weeks.length - 1 : Math.min(weekIdx, weeks.length - 1)) : -1;
  const selWeek = curWeek >= 0 ? weeks[curWeek] : null;

  // Per-outlet ratings for the calendar-selected week (x-axis = outlets).
  const outletSeries = useMemo(
    () =>
      (selWeek?.outlets ?? []).map((o) => ({
        name: o.name,
        Zomato: o.zomato?.rating ?? null,
        Swiggy: o.swiggy?.rating ?? null,
        Google: o.google?.rating ?? null,
      })),
    [selWeek]
  );

  const pickWeekByDate = (value: string) => {
    if (!value) return;
    const mon = isoMondayOf(value);
    const i = weeks.findIndex((w) => w.weekStart === mon);
    if (i >= 0) setWeekIdx(i);
  };

  // Per-platform network averages + totals.
  const platformStats = useMemo(() => {
    const outlets = data?.outlets ?? [];
    return PLATFORMS.map((p) => {
      const ratings = outlets
        .map((o) => o[p.key].rating)
        .filter((r): r is number => typeof r === 'number');
      const reviews = outlets
        .map((o) => o[p.key].reviews)
        .filter((r): r is number => typeof r === 'number');
      return {
        ...p,
        avg: avg(ratings),
        totalReviews: reviews.length ? reviews.reduce((a, b) => a + b, 0) : null,
        listed: ratings.length,
      };
    });
  }, [data]);

  // Combined average per outlet (across the three platforms).
  const outletScore = (o: OutletRating): number | null =>
    avg([o.zomato.rating, o.swiggy.rating, o.google.rating].filter((r): r is number => typeof r === 'number'));

  const networkAvg = useMemo(() => {
    const scores = (data?.outlets ?? []).map(outletScore).filter((s): s is number => s != null);
    return avg(scores);
  }, [data]);

  const bestOutlet = useMemo(() => {
    let best: { name: string; score: number } | null = null;
    for (const o of data?.outlets ?? []) {
      const s = outletScore(o);
      if (s != null && (!best || s > best.score)) best = { name: o.name, score: s };
    }
    return best;
  }, [data]);

  const sortedOutlets = useMemo(() => {
    const outlets = [...(data?.outlets ?? [])];
    outlets.sort((a, b) => {
      const sa = sortBy === 'overall' ? outletScore(a) : a[sortBy].rating;
      const sb = sortBy === 'overall' ? outletScore(b) : b[sortBy].rating;
      return (sb ?? -1) - (sa ?? -1);
    });
    return outlets;
  }, [data, sortBy]);

  const chartData = useMemo(
    () =>
      sortedOutlets.map((o) => ({
        name: o.name,
        Zomato: o.zomato.rating,
        Swiggy: o.swiggy.rating,
        Google: o.google.rating,
      })),
    [sortedOutlets]
  );

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand" />
          Loading ratings…
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-3 text-slate-500">
        <p>Couldn’t load ratings.</p>
        <button onClick={load} className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Outlet Ratings</h1>
          <p className="mt-1 text-sm text-slate-500">
            Zomato, Swiggy &amp; Google ratings across {data.outlets.length} outlets
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <span>Updated {relativeUpdated(data.updatedAt)} IST</span>
          <button
            onClick={load}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-medium text-slate-600 shadow-sm transition hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {data.isSample && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 animate-fade-in">
          Showing <strong>sample data</strong>. Once the daily scraper is wired to your outlet URLs, real ratings appear here automatically.
        </div>
      )}

      {/* Platform KPI cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {platformStats.map((p) => (
          <div
            key={p.key}
            className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card transition hover:shadow-card-hover animate-slide-up"
          >
            <div className="h-1.5 w-full" style={{ backgroundColor: p.color }} />
            <div className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">{p.label}</span>
                <span
                  className="rounded-full px-2 py-0.5 text-xs font-medium"
                  style={{ backgroundColor: `${p.color}1A`, color: p.color }}
                >
                  {p.listed} outlets
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-4xl font-bold tabular-nums text-slate-900">{fmt(p.avg)}</span>
                <span className="text-sm text-slate-400">/ 5 avg</span>
              </div>
              <div className="mt-2">
                <Stars value={p.avg} color={p.color} />
              </div>
              <div className="mt-3 text-xs text-slate-500">
                {fmtInt(p.totalReviews)} total reviews
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Network summary strip */}
      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-50 to-white p-5 shadow-card">
          <p className="text-xs font-medium uppercase tracking-wide text-brand-700">Network average</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold tabular-nums text-slate-900">{fmt(networkAvg, 2)}</span>
            <span className="text-sm text-slate-400">/ 5</span>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Top-rated outlet</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-900">{bestOutlet?.name ?? '—'}</span>
            {bestOutlet && (
              <span className="text-sm font-semibold text-brand">{fmt(bestOutlet.score, 2)}</span>
            )}
          </div>
        </div>
      </div>

      {/* Weekly ratings trend (all outlets) */}
      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-800">Ratings by outlet</h2>
            <p className="mt-0.5 text-xs text-slate-400">
              Zomato, Swiggy &amp; Google for each outlet &middot; pick a date with the calendar
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setWeekIdx(Math.max(0, (curWeek < 0 ? 0 : curWeek) - 1))}
              disabled={curWeek <= 0}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition hover:bg-slate-50 disabled:opacity-40"
              aria-label="Previous week"
            >
              &lsaquo;
            </button>
            <div className="text-right">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400">Week</span>
                <input
                  type="date"
                  value={selWeek?.weekStart ?? ''}
                  onChange={(e) => pickWeekByDate(e.target.value)}
                  className="rounded-lg border border-slate-200 px-2 py-1 text-sm text-slate-700"
                />
              </div>
              {selWeek && (
                <div className="mt-0.5 text-xs text-slate-400">
                  <span className="font-semibold text-slate-700">{selWeek.weekStart}</span> to {selWeek.weekEnd}
                </div>
              )}
            </div>
            <button
              onClick={() => setWeekIdx(Math.min(weeks.length - 1, (curWeek < 0 ? weeks.length - 1 : curWeek) + 1))}
              disabled={curWeek < 0 || curWeek === weeks.length - 1}
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition hover:bg-slate-50 disabled:opacity-40"
              aria-label="Next week"
            >
              &rsaquo;
            </button>
          </div>
        </div>

        {selWeek && (
          <div className="mb-4 grid grid-cols-3 gap-3">
            {PLATFORMS.map((p) => (
              <div key={p.key} className="rounded-xl border border-slate-200 p-3">
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                  <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                  {p.label}
                </div>
                <div className="mt-1 text-2xl font-bold tabular-nums text-slate-900">
                  {fmt(selWeek.aggregate?.[p.key] ?? null, 2)}{' '}
                  <span className="text-xs font-medium text-slate-400">/ 5</span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="h-96 w-full">
          {outletSeries.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={outletSeries} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" vertical={false} />
                <XAxis dataKey="name" interval={0} angle={-30} textAnchor="end" height={90} tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#e2e8f0' }} />
                <YAxis domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} tick={{ fontSize: 12, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }} />
                <Legend wrapperStyle={{ fontSize: 13, paddingTop: 8 }} />
                <Line type="monotone" dataKey="Zomato" stroke={platformMeta('zomato').color} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} connectNulls />
                <Line type="monotone" dataKey="Swiggy" stroke={platformMeta('swiggy').color} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} connectNulls />
                <Line type="monotone" dataKey="Google" stroke={platformMeta('google').color} strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} connectNulls />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-center text-sm text-slate-400">
              No ratings recorded for the selected week.
            </div>
          )}
        </div>
      </div>

      {/* Per-outlet detail cards */}
      <h2 className="mt-8 mb-4 text-base font-semibold text-slate-800">Outlet detail</h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {sortedOutlets.map((o) => {
          const score = outletScore(o);
          return (
            <div
              key={o.name}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card transition hover:shadow-card-hover"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{o.name}</h3>
                  <p className="text-xs text-slate-400">{o.city}</p>
                </div>
                <div className="rounded-lg bg-brand-50 px-3 py-1.5 text-right">
                  <div className="text-lg font-bold leading-none text-brand-700">{fmt(score, 2)}</div>
                  <div className="text-[10px] uppercase tracking-wide text-brand-600">overall</div>
                </div>
              </div>
              <div className="mt-4 space-y-3">
                {PLATFORMS.map((p) => {
                  const pr = o[p.key];
                  return (
                    <div key={p.key} className="flex items-center justify-between gap-3">
                      <span className="w-16 shrink-0 text-sm font-medium" style={{ color: p.color }}>
                        {p.label}
                      </span>
                      <div className="flex flex-1 items-center gap-2">
                        <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{ width: `${((pr.rating ?? 0) / 5) * 100}%`, backgroundColor: p.color }}
                          />
                        </div>
                        <span className="w-9 shrink-0 text-right text-sm font-semibold tabular-nums text-slate-800">
                          {fmt(pr.rating)}
                        </span>
                      </div>
                      <span className="w-20 shrink-0 text-right text-xs text-slate-400">
                        {fmtInt(pr.reviews)} rev
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
