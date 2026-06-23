'use client';

import Link from 'next/link';
import { useKotHref } from './DashboardNav';

/* ── SVG icon components ── */

function SalesIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M3 3v18h18" />
      <path d="M7 16l4-4 4 4 6-6" />
    </svg>
  );
}

function DiscountIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <circle cx="9" cy="9" r="2" />
      <circle cx="15" cy="15" r="2" />
      <path d="M7.5 16.5L16.5 7.5" />
      <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function DelayIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function DailyIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}

function WeeklyIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
    </svg>
  );
}

function KotIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M9 4h6a1 1 0 011 1v1a1 1 0 01-1 1H9a1 1 0 01-1-1V5a1 1 0 011-1z" />
      <path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

function RatingsIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function ExternalArrow() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path fillRule="evenodd" d="M5.22 14.78a.75.75 0 001.06 0l7.22-7.22v5.69a.75.75 0 001.5 0v-7.5a.75.75 0 00-.75-.75h-7.5a.75.75 0 000 1.5h5.69l-7.22 7.22a.75.75 0 000 1.06z" clipRule="evenodd" />
    </svg>
  );
}

function ChevronRight() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
      <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
    </svg>
  );
}

/* ── URL builders (same logic as DashboardNav) ── */

const DAILY_SHEET_ID = '1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs';
const DAY_GIDS: Record<number, string> = {
  0: '1531957147', 1: '417033488', 2: '2078196306',
  3: '1189627705', 4: '169886895', 5: '1816270025', 6: '1918686710',
};

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

const KOT_SHEET_ID = '1yOYpZBjohebpfpjRIfrDnUNd21bDcFcbt2vem1D_mn8';
const KOT_FALLBACK_URL = `https://docs.google.com/spreadsheets/d/${KOT_SHEET_ID}/edit`;

/* ── Card data ── */

type CardDef =
  | { href: string; label: string; desc: string; icon: React.ReactNode; accent: string; internal: true }
  | { hrefFactory: () => string; label: string; desc: string; icon: React.ReactNode; accent: string; external: true; kot?: boolean };

const CARDS: CardDef[] = [
  {
    href: '/dashboard/sales-item',
    label: 'Sales Item Dashboard',
    desc: 'Full product-level sales analytics with trends, category breakdowns, and performance metrics.',
    icon: <SalesIcon />,
    accent: 'from-emerald-500 to-green-600',
    internal: true,
  },
  {
    href: '/dashboard/discount-codes',
    label: 'Discount Codes',
    desc: 'Daily discount code tracking with calendar view. See which codes are active and their impact.',
    icon: <DiscountIcon />,
    accent: 'from-violet-500 to-purple-600',
    internal: true,
  },
  {
    href: '/dashboard/delay',
    label: 'Delay Dashboard',
    desc: 'Monitor delivery delays, identify bottlenecks, and track on-time performance across outlets.',
    icon: <DelayIcon />,
    accent: 'from-amber-500 to-orange-600',
    internal: true,
  },
  {
    href: '/dashboard/ratings',
    label: 'Ratings',
    desc: 'Zomato, Swiggy & Google ratings for every outlet — compare platforms and spot which locations need attention.',
    icon: <RatingsIcon />,
    accent: 'from-teal-500 to-cyan-600',
    internal: true,
  },
  {
    hrefFactory: buildDailyUrl,
    label: 'Daily Dashboard',
    desc: 'Yesterday\'s key numbers — revenue, orders, and operational stats in the daily sales sheet.',
    icon: <DailyIcon />,
    accent: 'from-sky-500 to-blue-600',
    external: true,
  },
  {
    hrefFactory: buildWeeklyUrl,
    label: 'Weekly Dashboard',
    desc: 'Week-over-week trends and aggregated performance. Opens last week\'s tab in Google Sheets.',
    icon: <WeeklyIcon />,
    accent: 'from-rose-500 to-pink-600',
    external: true,
  },
  {
    hrefFactory: () => KOT_FALLBACK_URL,
    label: 'Daily KOT Comparison',
    desc: 'Total Dine In/Pickup KOT vs Captain App KOT per outlet. Opens the latest day\'s tab automatically.',
    icon: <KotIcon />,
    accent: 'from-indigo-500 to-blue-600',
    external: true,
    kot: true,
  },
];

/* ── Component ── */

export default function DashboardCards() {
  const kotHref = useKotHref();
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {CARDS.map((card, i) => {
        const isExternal = 'external' in card;
        const href = isExternal
          ? 'kot' in card && card.kot
            ? kotHref
            : card.hrefFactory()
          : card.href;

        const cardContent = (
          <div
            className="group relative flex flex-col bg-white rounded-xl border border-slate-200/80
                        shadow-card hover:shadow-card-hover hover:border-slate-300
                        transition-all duration-300 overflow-hidden h-full"
            style={{ animationDelay: `${i * 80}ms` }}
          >
            {/* Accent top bar */}
            <div className={`h-1 w-full bg-gradient-to-r ${card.accent}`} />

            <div className="flex flex-col flex-1 p-5">
              {/* Icon + badge row */}
              <div className="flex items-start justify-between">
                <div className={`flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br ${card.accent} text-white shadow-sm`}>
                  {card.icon}
                </div>
                {isExternal && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
                    Google Sheets
                    <ExternalArrow />
                  </span>
                )}
              </div>

              {/* Title */}
              <h3 className="mt-4 text-base font-semibold text-slate-900 group-hover:text-brand-700 transition-colors">
                {card.label}
              </h3>

              {/* Description */}
              <p className="mt-1.5 text-sm text-slate-500 leading-relaxed flex-1">
                {card.desc}
              </p>

              {/* CTA row */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center text-sm font-medium text-brand-600 group-hover:text-brand-700 transition-colors">
                {isExternal ? 'Open in Sheets' : 'View dashboard'}
                <span className="ml-1 transition-transform group-hover:translate-x-0.5">
                  {isExternal ? <ExternalArrow /> : <ChevronRight />}
                </span>
              </div>
            </div>
          </div>
        );

        if (isExternal) {
          return (
            <a key={card.label} href={href} target="_blank" rel="noopener noreferrer" className="block h-full">
              {cardContent}
            </a>
          );
        }

        return (
          <Link key={card.label} href={href} className="block h-full">
            {cardContent}
          </Link>
        );
      })}
    </div>
  );
}
