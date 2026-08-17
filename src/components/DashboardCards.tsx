'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useKotHref, useWeeklyKotHref, useMonthlyKotHref } from './DashboardNav';

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

function WeeklyKotIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M9 4h6a1 1 0 011 1v1a1 1 0 01-1 1H9a1 1 0 01-1-1V5a1 1 0 011-1z" />
      <path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
      <path d="M8 13h3M8 17h6" />
    </svg>
  );
}

function MonthlyKotIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M9 4h6a1 1 0 011 1v1a1 1 0 01-1 1H9a1 1 0 01-1-1V5a1 1 0 011-1z" />
      <path d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
      <path d="M8 11h8M8 15h8M11 11v6" />
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

function FeedbackIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
      <path d="M8 9h8M8 13h5" />
    </svg>
  );
}

function MomosIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M3 17a9 9 0 0118 0" />
      <path d="M3 17h18" />
      <path d="M7.5 17V9.6M12 17V7.8M16.5 17V9.6" />
    </svg>
  );
}

function MusicIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    </svg>
  );
}

function VehicleIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="w-6 h-6">
      <path d="M1 3h13v10H1z" />
      <path d="M14 8h4l3 3v2h-7z" />
      <circle cx="5.5" cy="16.5" r="1.5" />
      <circle cx="17.5" cy="16.5" r="1.5" />
      <path d="M7 16.5h9" />
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

function EyeIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
      <path d="M1.5 12s3.5-7 10.5-7 10.5 7 10.5 7-3.5 7-10.5 7S1.5 12 1.5 12z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M18 6L6 18M6 6l12 12" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
      <circle cx="12" cy="12" r="9" />
      <polyline points="12 7 12 12 15 14" />
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
const KOT_WEEKLY_SHEET_ID = '1eFBNV1bAwXqATegto9k0S2N9KfCGAtyufmbkpbzQX30';
const KOT_WEEKLY_FALLBACK_URL = `https://docs.google.com/spreadsheets/d/${KOT_WEEKLY_SHEET_ID}/edit`;
const KOT_MONTHLY_SHEET_ID = '1TFCNxjX_0AGV2t2fkK_KzCMf3W9uMdSdVGbVB7_Nofw';
const KOT_MONTHLY_FALLBACK_URL = `https://docs.google.com/spreadsheets/d/${KOT_MONTHLY_SHEET_ID}/edit`;

const MOMOS_DASHBOARD_URL = '/nutriobox-momos-dashboard.html';

/* ── Workflow algorithm flows (built from each tile's Claude scheduled task) ──
   Rendered as a top-to-bottom flowchart: STAGE heading, sub-lines, optional
   ├── branches, then a │ connector (with an edge label) and a ▼ to the next. */

type FlowNode = {
  stage: string;
  lines?: string[];
  edge?: string;
  branches?: string[];
};

type Flow = {
  automated: boolean;
  tasks: string[];
  schedule: string;
  nodes: FlowNode[];
};

const FLOWS: Record<string, Flow> = {
  'Sales Item Dashboard': {
    automated: true,
    tasks: ['nutriobox-daily-data-v2 (Playwright)'],
    schedule: '04:00 & 16:00 IST',
    nodes: [
      { stage: 'WINDOWS TASK SCHEDULER', lines: ['NutrioBox-DailyData-AM / PM'], edge: '04:00 & 16:00 IST · refresh sessions' },
      { stage: 'PETPOOJA — ORDER SUMMARY CSV', lines: ['Playwright export ×2 (sync-lag)'], edge: 'larger CSV wins' },
      { stage: 'DEDUPE → INVOICE LEVEL', lines: ['key = (restaurant, invoice_no)'], edge: 'Success + Cancelled' },
      { stage: 'ADD-ONS — REPORT 31', lines: ['Playwright scrape, all 10 outlets'],
        branches: ['DLF Phase 2', 'Rajinder Nagar', 'Dwarka · Janakpuri · Noida …', '+ 6 more outlets'],
        edge: 'sums verified vs page Total' },
      { stage: 'RECONCILE (morning only)', lines: ['export total vs POS dashboard'], edge: 're-export if > ₹200 short' },
      { stage: 'REBUILD DAILY_DATA', lines: ['drop target day · keep <08:00 tail'], edge: 'prev-day sales must stay identical' },
      { stage: 'PUBLISH', lines: ['gzip → Supabase → hash-verify'], edge: '' },
      { stage: 'LIVE DASHBOARD', lines: ['operationsdashboard.nutriobox.com'] },
    ],
  },

  'Discount Codes': {
    automated: true,
    tasks: ['daily-offer-tracker', 'nutriobox-discount-report-daily-upload'],
    schedule: '04:09 + 05:00 IST',
    nodes: [
      { stage: 'SCHEDULE · 04:09 IST', lines: ['daily-offer-tracker'], edge: 'freshness: current-day only' },
      { stage: 'ZOMATO — track-offers API', lines: ['10 res IDs'],
        branches: ['Standard codes (NutrioBox)', 'Extra codes (platform)'], edge: '' },
      { stage: 'SWIGGY — GraphQL /query', lines: ['10 RIDs · access_token'], edge: 'retry 5 / 10 / 15 min on fail' },
      { stage: 'BUILD HTML EMAIL', lines: ['inline CSS · Standard vs Extra bands'], edge: 'quality checks (all blocking)' },
      { stage: 'SEND via Apps Script', lines: ['→ mayank@nutriobox.com'], edge: 'no report if data stale' },
      { stage: 'SCHEDULE · 05:00 IST', lines: ['fetch that email → wrap HTML'], edge: '' },
      { stage: 'SUPABASE', lines: ['reports/discount-codes-<date>.html'], edge: '' },
      { stage: 'DISCOUNT CODES TILE', lines: ['calendar view'] },
    ],
  },

  'Delay Dashboard': {
    automated: true,
    tasks: ['nutriobox-weekly-delay-dashboard'],
    schedule: 'Wed 06:00 IST',
    nodes: [
      { stage: 'SCHEDULE · WED 06:00 IST', edge: 'prior completed Mon–Sun' },
      { stage: 'GOOGLE SHEET (delay tab)', lines: ['fetch as CSV → cols T / U / V / W'], edge: 'tab existence check (mandatory)' },
      { stage: 'APPEND WEEK', lines: ['both local HTML copies'], edge: 'verify md5 identical · NO gzip' },
      { stage: 'SUPABASE', lines: ['reports/delay-dashboard.html'], edge: '' },
      { stage: 'DELAY DASHBOARD', lines: ['/dashboard/delay'] },
    ],
  },

  'Customer Feedback': {
    automated: false,
    tasks: [],
    schedule: 'internal page',
    nodes: [
      { stage: 'INTERNAL PAGE', lines: ['no scheduled Claude task'], edge: 'served by the app itself' },
      { stage: 'CUSTOMER FEEDBACK TILE', lines: ['sentiment + themes across outlets'] },
    ],
  },

  'Ratings': {
    automated: true,
    tasks: ['nutriobox-ratings-weekly-refresh'],
    schedule: 'Mon 08:07 IST',
    nodes: [
      { stage: 'SCHEDULE · MON 08:07 IST', edge: 'baseline ratings.json (keep prior on fail)' },
      { stage: 'SCRAPE PER OUTLET (×10)',
        branches: ['Google — knowledge panel', 'Zomato — JSON-LD aggregateRating', 'Swiggy — dineout / delivery'], edge: '' },
      { stage: 'UPLOAD JSON', lines: ['ratings.json + ratings-history.json'], edge: 'verify /api/ratings' },
      { stage: 'RATINGS TILE', lines: ['platform compare + weekly trend'] },
    ],
  },

  'Music Monitor': {
    automated: false,
    tasks: [],
    schedule: 'live monitor',
    nodes: [
      { stage: 'LIVE MONITOR', lines: ['no scheduled task'], edge: 'real-time device state · 9 outlets' },
      { stage: 'MUSIC MONITOR TILE', lines: ['Bluetooth / laptop / off — hour by hour'] },
    ],
  },

  'Vehicle Monitoring Dashboard': {
    automated: false,
    tasks: [],
    schedule: 'live GPS feed',
    nodes: [
      { stage: 'ONELAP GPS FEED', lines: ['live · no scheduled task'], edge: 'route · outlet stops · drive vs halt' },
      { stage: 'VEHICLE MONITORING TILE', lines: ['per-vehicle trip log'] },
    ],
  },

  'Daily Dashboard': {
    automated: true,
    tasks: ['petpooja-sales-to-gsheet'],
    schedule: 'Daily 10:30 IST',
    nodes: [
      { stage: 'SCHEDULE · 10:30 IST', edge: 'yesterday' },
      { stage: 'PETPOOJA POS DASHBOARD', lines: ['summary cards + per-outlet table'], edge: 'Zomato / Swiggy split' },
      { stage: 'SALES DATA SHEET', lines: ['day-of-week tab · target row'],
        branches: ['B–K: 10 outlet totals', 'L = SUM · N = NetSales', 'O / S / U: % · AOV formulas'],
        edge: 'verify (1 screenshot)' },
      { stage: 'DAILY DASHBOARD', lines: ['opens the Google Sheet'] },
    ],
  },

  'Weekly Dashboard': {
    automated: true,
    tasks: ['weekly-petpooja-sales-report', 'petpooja-weekly-sales-sync', 'weekly-petpooja-dining-delivery-update'],
    schedule: 'Wed 03:00 + Mon',
    nodes: [
      { stage: 'SCHEDULE · WED 03:00 IST', lines: ['full weekly entry'], edge: 'last complete Mon–Sun' },
      { stage: 'PETPOOJA SUB-ORDER WISE', lines: ['orders / sales / platform split'], edge: '→ cols D–S' },
      { stage: 'PETPOOJA KOT DELAY', lines: ['15–25 min · 26+ min'], edge: '→ cols T–W' },
      { stage: 'ZOMATO FUNNEL + SWIGGY xlsx', edge: '→ X–AH · AI–AR' },
      { stage: 'CAPTAIN KOT', edge: '→ AS–AU · read-back throws on blank' },
      { stage: 'WEEKLY SALES SHEET', lines: ['+ Mon 12:30 · Total Sales sync', '+ Mon 08:00 · dining / delivery %'], edge: '' },
      { stage: 'WEEKLY DASHBOARD', lines: ['opens the Google Sheet'] },
    ],
  },

  'Daily KOT Comparison': {
    automated: true,
    tasks: ['daily-kot-comparison'],
    schedule: 'Daily 05:10 IST',
    nodes: [
      { stage: 'SCHEDULE · 05:10 IST', edge: 'yesterday' },
      { stage: 'PETPOOJA KOT LIST', lines: ['order type [Pickup, Dine In]'],
        branches: ['9 outlets → col B (Total KOT)'], edge: '' },
      { stage: 'CAPTAIN REPORT', lines: ['Total “No of Kots”'], edge: '→ col C' },
      { stage: 'NEW DATED TAB', lines: ['source sheet · mirror to Sales Data'], edge: '' },
      { stage: 'POINTER', lines: ['kot-latest.json → newest gid'], edge: '' },
      { stage: 'DAILY KOT TILE', lines: ['opens the latest tab'] },
    ],
  },

  'Weekly KOT Comparison': {
    automated: true,
    tasks: ['kot-comparsion'],
    schedule: 'Mon 11:06 IST',
    nodes: [
      { stage: 'SCHEDULE · MON 11:06 IST', edge: 'last completed Mon–Sun' },
      { stage: 'PETPOOJA KOT + CAPTAIN', lines: ['9 outlets · [Mon 13:00 → Mon 13:00)'], edge: 'col B + col C' },
      { stage: 'DUPLICATE NEWEST TAB', lines: ['rename to week · move leftmost'], edge: 'fill B2:B10 / C2:C10' },
      { stage: 'POINTER', lines: ['kot-weekly-latest.json'], edge: '' },
      { stage: 'WEEKLY KOT TILE', lines: ['opens the latest tab'] },
    ],
  },

  'Monthly KOT Comparison': {
    automated: true,
    tasks: ['monthly-kot-comparison'],
    schedule: '1st of month 11:00 IST',
    nodes: [
      { stage: 'SCHEDULE · 1st · 11:00 IST', edge: 'previous calendar month' },
      { stage: 'PETPOOJA KOT + CAPTAIN', lines: ['9 outlets · month range'], edge: 'idempotent on month tab' },
      { stage: 'MONTHLY KOT SHEET', lines: ['“<Month> <Year>” tab · cols B / C'], edge: '' },
      { stage: 'MONTHLY KOT TILE', lines: ['opens the latest tab'] },
    ],
  },

  'Momos Weekly Performance': {
    automated: true,
    tasks: ['nutriobox-momos-dashboard--weekly-update-higgsfield'],
    schedule: 'Mon 05:45 IST',
    nodes: [
      { stage: 'SCHEDULE · MON 05:45 IST', edge: 'last Mon–Sun' },
      { stage: 'PETPOOJA ORDER SUMMARY CSV', lines: ['10 outlets'], edge: 'filter Whole Wheat Momos (6 SKUs)' },
      { stage: 'COMPUTE WEEK',
        branches: ['veg / non-veg', 'Steamed / Tandoori / Chilli', 'sales · units · orders · AOV'], edge: '' },
      { stage: 'EDIT HIGGSFIELD APP', lines: ['const D → append 1 week'], edge: 'sanity ~₹7L · commit + push' },
      { stage: 'DEPLOY', lines: ['nutriobox-momos.higgsfield.app'], edge: '' },
      { stage: 'MOMOS TILE', lines: ['linked from this card'] },
    ],
  },
};

/* ── Card data ── */

type CardDef =
  | { href: string; label: string; desc: string; icon: React.ReactNode; accent: string; internal: true }
  | { hrefFactory: () => string; label: string; desc: string; icon: React.ReactNode; accent: string; external: true; kot?: boolean; kotWeekly?: boolean; kotMonthly?: boolean; badge?: string; cta?: string };

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
    href: '/dashboard/feedback',
    label: 'Customer Feedback',
    desc: 'Customer feedback and satisfaction insights across outlets — spot recurring themes and track sentiment over time.',
    icon: <FeedbackIcon />,
    accent: 'from-blue-500 to-indigo-600',
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
    href: '/dashboard/music',
    label: 'Music Monitor',
    desc: 'Live background-music monitor for all 9 outlets — see which are playing on Bluetooth, on a laptop speaker, or not playing at all, hour by hour.',
    icon: <MusicIcon />,
    accent: 'from-green-500 to-emerald-600',
    internal: true,
  },
  {
    href: '/dashboard/vehicle-monitoring',
    label: 'Vehicle Monitoring Dashboard',
    desc: 'Live delivery-fleet tracking from OneLap GPS — each vehicle\'s route, outlet stops, drive vs halt times, and a full trip log per leg.',
    icon: <VehicleIcon />,
    accent: 'from-cyan-500 to-blue-600',
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
  {
    hrefFactory: () => KOT_WEEKLY_FALLBACK_URL,
    label: 'Weekly KOT Comparison',
    desc: 'Weekly Dine In/Pickup KOT vs Captain App KOT per outlet. Opens the latest week\'s tab automatically.',
    icon: <WeeklyKotIcon />,
    accent: 'from-fuchsia-500 to-purple-600',
    external: true,
    kotWeekly: true,
  },
  {
    hrefFactory: () => KOT_MONTHLY_FALLBACK_URL,
    label: 'Monthly KOT Comparison',
    desc: 'Monthly Dine In/Pickup KOT vs Captain App KOT per outlet. Opens the latest month\'s tab automatically.',
    icon: <MonthlyKotIcon />,
    accent: 'from-purple-500 to-indigo-600',
    external: true,
    kotMonthly: true,
  },
  {
    hrefFactory: () => MOMOS_DASHBOARD_URL,
    label: 'Momos Weekly Performance',
    desc: 'Weekly momo sales, units sold, and veg vs non-veg mix across outlets — variants and week-over-week trends.',
    icon: <MomosIcon />,
    accent: 'from-orange-500 to-red-600',
    external: true,
    badge: 'Live Dashboard',
    cta: 'Open dashboard',
  },
];

/* ── Workflow modal — renders the flow as a top-to-bottom algorithm ── */

function WorkflowModal({
  label,
  accent,
  onClose,
}: {
  label: string;
  accent: string;
  onClose: () => void;
}) {
  const flow = FLOWS[label];
  if (!flow) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${label} workflow`}
    >
      <div
        className="relative w-full max-w-xl max-h-[86vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`h-1.5 w-full bg-gradient-to-r ${accent} rounded-t-2xl`} />

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 px-6 pt-5 pb-4 bg-white/95 backdrop-blur border-b border-slate-100">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900">{label}</h2>
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                  flow.automated
                    ? 'text-emerald-700 bg-emerald-50 border-emerald-100'
                    : 'text-slate-500 bg-slate-50 border-slate-200'
                }`}
              >
                {flow.automated ? 'Automated' : 'Live / manual'}
              </span>
              <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full border border-brand-100">
                <ClockIcon />
                {flow.schedule}
              </span>
            </div>
            {flow.tasks.length > 0 && (
              <div className="mt-1 text-[11px] text-slate-400 font-mono truncate">
                {flow.tasks.join('  ·  ')}
              </div>
            )}
          </div>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="shrink-0 flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <CloseIcon />
          </button>
        </div>

        {/* Flowchart panel */}
        <div className="px-5 py-5">
          <div className="rounded-xl bg-slate-900 text-slate-100 px-5 py-5 font-mono text-[12.5px] leading-[1.5] overflow-x-auto">
            {flow.nodes.map((n, i) => {
              const branches = n.branches ?? [];
              const isLastNode = i === flow.nodes.length - 1;
              return (
                <div key={i}>
                  <div className="font-bold tracking-wide text-white whitespace-pre">{n.stage}</div>
                  {(n.lines ?? []).map((l, j) => (
                    <div key={j} className="text-slate-400 whitespace-pre-wrap">{l}</div>
                  ))}
                  {branches.map((b, j) => (
                    <div key={j} className="text-emerald-300/90 whitespace-pre-wrap">
                      {(j === branches.length - 1 ? '└── ' : '├── ') + b}
                    </div>
                  ))}
                  {!isLastNode && (
                    <div className="text-slate-500 select-none">
                      <div className="whitespace-pre">│</div>
                      {n.edge ? (
                        <div className="whitespace-pre-wrap">
                          {'│   '}
                          <span className="italic text-slate-400">{n.edge}</span>
                        </div>
                      ) : null}
                      <div className="text-sky-300 whitespace-pre">▼</div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p className="mt-3 text-[11px] text-slate-400">
            {flow.automated
              ? 'This is the algorithm the scheduled Claude task runs each cycle.'
              : 'How this tile stays current (no scheduled task).'}
          </p>
        </div>
      </div>
    </div>
  );
}

/* ── Component ── */

export default function DashboardCards() {
  const kotHref = useKotHref();
  const weeklyKotHref = useWeeklyKotHref();
  const monthlyKotHref = useMonthlyKotHref();
  const [activeLabel, setActiveLabel] = useState<string | null>(null);

  const activeCard = CARDS.find((c) => c.label === activeLabel) || null;

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {CARDS.map((card, i) => {
          const isExternal = 'external' in card;
          const href = isExternal
            ? 'kot' in card && card.kot
              ? kotHref
              : 'kotWeekly' in card && card.kotWeekly
              ? weeklyKotHref
              : 'kotMonthly' in card && card.kotMonthly
              ? monthlyKotHref
              : card.hrefFactory()
            : card.href;

          const hasWorkflow = card.label in FLOWS;

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
                  <div className="flex items-center gap-2">
                    {isExternal && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
                        {card.badge ?? 'Google Sheets'}
                        <ExternalArrow />
                      </span>
                    )}
                    {hasWorkflow && (
                      <button
                        type="button"
                        aria-label={`View workflow for ${card.label}`}
                        title="View workflow"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          setActiveLabel(card.label);
                        }}
                        className="relative z-10 flex items-center justify-center w-7 h-7 rounded-lg text-slate-400
                                   bg-white border border-slate-200 hover:text-brand-600 hover:border-brand-300 hover:bg-brand-50
                                   transition-colors"
                      >
                        <EyeIcon />
                      </button>
                    )}
                  </div>
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
                  {isExternal ? (card.cta ?? 'Open in Sheets') : 'View dashboard'}
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

      {activeCard && (
        <WorkflowModal
          label={activeCard.label}
          accent={activeCard.accent}
          onClose={() => setActiveLabel(null)}
        />
      )}
    </>
  );
}
