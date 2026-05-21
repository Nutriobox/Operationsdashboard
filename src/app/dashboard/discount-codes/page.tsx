// Discount Codes page - daily offer tracker report with a date picker.
//
// A small calendar in the top right lets users pick any date. The iframe
// below loads /api/discount-codes-report?date=YYYY-MM-DD, which streams the
// matching report from Supabase Storage. If no report exists for the chosen
// date, the API serves a friendly "No report available" placeholder.
//
// On mount, the page asks /api/discount-codes-latest for the most recent
// date that has a report and defaults the picker to that. This way the user
// sees the freshest available report even if today's email hasn't arrived
// yet (in which case "latest" will be yesterday).
'use client';

import { useEffect, useMemo, useState } from 'react';

function todayInIst(): string {
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const now = new Date(Date.now() + IST_OFFSET_MS);
  return now.toISOString().slice(0, 10);
}

function formatPretty(isoDate: string): string {
  // YYYY-MM-DD -> "20 May 2026"
  const [y, m, d] = isoDate.split('-').map(Number);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${d} ${months[m - 1]} ${y}`;
}

export default function DiscountCodesPage() {
  const today = useMemo(todayInIst, []);
  // Start at today; if /api/discount-codes-latest returns a different
  // (typically older) most-recent date and the user hasn't manually picked,
  // we jump to that. We also flip an init flag so the user's manual picks
  // aren't overwritten on a slow API response.
  const [date, setDate] = useState<string>(today);
  const [userPicked, setUserPicked] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch('/api/discount-codes-latest', { cache: 'no-store' })
      .then((r) => r.json())
      .then((j: { latestDate?: string | null }) => {
        if (cancelled || userPicked) return;
        if (j.latestDate && j.latestDate !== date) {
          setDate(j.latestDate);
        }
      })
      .catch(() => {/* fall back to today */});
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onChangeDate = (newDate: string) => {
    setUserPicked(true);
    setDate(newDate || today);
  };

  const iframeSrc = `/api/discount-codes-report?date=${date}`;
  // Header strip is 3rem (h-12). Top navbar is 3.5rem (h-14).
  const iframeHeight = 'calc(100vh - 3.5rem - 3rem)';

  return (
    <div className="flex flex-col bg-white" style={{ height: 'calc(100vh - 3.5rem)' }}>
      <div className="h-12 flex items-center justify-between px-4 border-b border-slate-200 bg-white">
        <div className="text-sm font-medium text-slate-700">
          Daily Offer Tracker
          <span className="ml-2 text-slate-400">·</span>
          <span className="ml-2 text-slate-500">{formatPretty(date)}</span>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <span className="hidden sm:inline">Date:</span>
          <input
            type="date"
            value={date}
            max={today}
            onChange={(e) => onChangeDate(e.target.value)}
            className="px-2 py-1 rounded border border-slate-300 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </label>
      </div>
      <iframe
        key={date}
        src={iframeSrc}
        title={`Discount Codes - ${date}`}
        className="block w-full border-0 bg-white"
        style={{ height: iframeHeight }}
      />
    </div>
  );
}
