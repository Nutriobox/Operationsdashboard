'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

// Daily Dashboard: which weekday tab in the Sales Data sheet to open.
// "Daily" means yesterday's tab — today's numbers aren't finalized yet.
const DAILY_SHEET_ID = '1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs';
const DAY_GIDS: Record<number, string> = {
  0: '1531957147', // Sun
  1: '417033488',  // Mon
  2: '2078196306', // Tues
  3: '1189627705', // Wed
  4: '169886895',  // Thur
  5: '1816270025', // Fri
  6: '1918686710', // Sat
};

// Weekly Dashboard: which week's tab to open. When a new week's tab gets
// added to the Weekly Sales sheet, prepend a new entry with the Monday's
// YYYY-MM-DD and the gid copied from the sheet tab URL.
const WEEKLY_SHEET_ID = '1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc';
const WEEKLY_GIDS: Array<{ startMonday: string; gid: string }> = [
  { startMonday: '2026-05-11', gid: '282654557' },
];

function buildDailyUrl(): string {
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const yesterdayIst = new Date(Date.now() + IST_OFFSET_MS - 24 * 60 * 60 * 1000);
  const gid = DAY_GIDS[yesterdayIst.getUTCDay()];
  return `https://docs.google.com/spreadsheets/d/${DAILY_SHEET_ID}/edit?gid=${gid}#gid=${gid}`;
}

function buildWeeklyUrl(): string {
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const nowIst = new Date(Date.now() + IST_OFFSET_MS);
  const daysToThisMonday = (nowIst.getUTCDay() + 6) % 7;
  const thisMonday = new Date(nowIst);
  thisMonday.setUTCDate(thisMonday.getUTCDate() - daysToThisMonday);
  const lastMonday = new Date(thisMonday);
  lastMonday.setUTCDate(lastMonday.getUTCDate() - 7);
  const lastMondayKey = lastMonday.toISOString().slice(0, 10);
  const sorted = [...WEEKLY_GIDS].sort((a, b) => b.startMonday.localeCompare(a.startMonday));
  const match = sorted.find((e) => e.startMonday <= lastMondayKey) || sorted[0];
  return `https://docs.google.com/spreadsheets/d/${WEEKLY_SHEET_ID}/edit?gid=${match.gid}#gid=${match.gid}`;
}

// Daily KOT Comparison: a brand-new dated tab (with a fresh Google gid) is
// created in this sheet every morning by the daily-kot-comparison task. That
// task publishes the newest tab's gid to a small public JSON on Supabase, which
// we fetch at runtime so this button always opens the latest tab. Until the
// fetch resolves (or if it fails) we fall back to the plain sheet URL.
const KOT_SHEET_ID = '1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8';
const KOT_LATEST_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/kot-latest.json';
const KOT_FALLBACK_URL = `https://docs.google.com/spreadsheets/d/${KOT_SHEET_ID}/edit`;

export function useKotHref(): string {
  const [href, setHref] = useState(KOT_FALLBACK_URL);
  useEffect(() => {
    let cancelled = false;
    fetch(`${KOT_LATEST_URL}?t=${Date.now()}`, { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (cancelled || !d || !d.gid) return;
        const id = d.sheetId || KOT_SHEET_ID;
        setHref(`https://docs.google.com/spreadsheets/d/${id}/edit?gid=${d.gid}#gid=${d.gid}`);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);
  return href;
}

// Each tab either navigates within the app (internal: true, uses next/link)
// or jumps straight to an external Google Sheet (external: true, uses a
// plain <a> tag with target="_blank" so the sheet opens in a new tab and
// the user doesn't lose the dashboard).
type Tab =
  | { href: string; label: string; internal: true }
  | { hrefFactory: () => string; label: string; external: true; kot?: boolean };

const TABS: Tab[] = [
  { href: '/dashboard/sales-item',    label: 'Sales Item Dashboard', internal: true },
  { href: '/dashboard/discount-codes',label: 'Discount Codes',       internal: true },
  { href: '/dashboard/delay',         label: 'Delay Dashboard',      internal: true },
  { href: '/dashboard/ratings',       label: 'Ratings',              internal: true },
  { hrefFactory: buildDailyUrl,       label: 'Daily Dashboard',      external: true },
  { hrefFactory: buildWeeklyUrl,      label: 'Weekly Dashboard',     external: true },
  { hrefFactory: () => KOT_FALLBACK_URL, label: 'Daily KOT Comparison', external: true, kot: true },
];

export default function DashboardNav() {
  const pathname = usePathname();
  const kotHref = useKotHref();

  return (
    <div className="flex justify-center px-4">
      <div className="inline-flex flex-wrap gap-1.5 rounded-xl bg-white border border-slate-200/80 p-1.5 shadow-sm backdrop-blur-sm">
        {TABS.map((t) => {
          if ('internal' in t) {
            const isActive = pathname === t.href || pathname.startsWith(t.href + '/');
            return (
              <Link
                key={t.label}
                href={t.href}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-brand text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {t.label}
              </Link>
            );
          }
          return (
            <a
              key={t.label}
              href={'kot' in t && t.kot ? kotHref : t.hrefFactory()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            >
              {t.label}
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" className="w-3 h-3 opacity-40">
                <path fillRule="evenodd" d="M4.22 11.78a.75.75 0 010-1.06L8.44 6.5H5.75a.75.75 0 010-1.5h4.5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0V7.56l-4.22 4.22a.75.75 0 01-1.06 0z" clipRule="evenodd" />
              </svg>
            </a>
          );
        })}
      </div>
    </div>
  );
}
