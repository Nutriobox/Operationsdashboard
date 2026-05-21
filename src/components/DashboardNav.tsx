'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

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

// Each tab either navigates within the app (internal: true, uses next/link)
// or jumps straight to an external Google Sheet (external: true, uses a
// plain <a> tag with target="_blank" so the sheet opens in a new tab and
// the user doesn't lose the dashboard).
type Tab =
  | { href: string; label: string; internal: true }
  | { hrefFactory: () => string; label: string; external: true };

const TABS: Tab[] = [
  { href: '/dashboard/sales-item',    label: 'Sales Item Dashboard', internal: true },
  { href: '/dashboard/discount-codes',label: 'Discount Codes',       internal: true },
  { href: '/dashboard/delay',         label: 'Delay Dashboard',      internal: true },
  { hrefFactory: buildDailyUrl,       label: 'Daily Dashboard',      external: true },
  { hrefFactory: buildWeeklyUrl,      label: 'Weekly Dashboard',     external: true },
];

export default function DashboardNav() {
  const pathname = usePathname();

  return (
    <div className="flex justify-center">
      <div className="inline-flex flex-wrap gap-2 rounded-full bg-white border border-slate-200 p-1.5 shadow-sm">
        {TABS.map((t) => {
          if ('internal' in t) {
            const isActive = pathname === t.href || pathname.startsWith(t.href + '/');
            return (
              <Link
                key={t.label}
                href={t.href}
                className={`px-5 py-2 text-sm font-medium rounded-full transition ${
                  isActive
                    ? 'bg-brand text-white shadow'
                    : 'text-slate-700 hover:bg-slate-100'
                }`}
              >
                {t.label}
              </Link>
            );
          }
          // External: skip the intermediate /dashboard/daily and
          // /dashboard/weekly pages entirely — go straight to Google Sheets.
          return (
            <a
              key={t.label}
              href={t.hrefFactory()}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2 text-sm font-medium rounded-full transition text-slate-700 hover:bg-slate-100"
            >
              {t.label}
            </a>
          );
        })}
      </div>
    </div>
  );
}
