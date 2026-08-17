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

/* ── Workflow steps — plain-English, step-by-step SOP for each tile.
   Written so someone new can follow the whole data flow and reproduce it. */

type Step = { title: string; body: string; bullets?: string[] };
type Flow = {
  automated: boolean;
  tasks: string[];
  schedule: string;
  intro: string;
  steps: Step[];
};

const FLOWS: Record<string, Flow> = {
  'Sales Item Dashboard': {
    automated: true,
    tasks: ['nutriobox-daily-data-v2 (Playwright automation)'],
    schedule: 'Every day at 4:00 AM & 4:00 PM IST',
    intro:
      'This dashboard shows product-level sales for all 10 NutrioBox outlets. It refreshes on its own twice a day: it pulls the raw order data from Petpooja (our billing/POS system), cleans it, and publishes it to the website. Nobody has to touch it.',
    steps: [
      {
        title: '1. The job starts automatically',
        body:
          'The office laptop runs a scheduled job at 4:00 AM and again at 4:00 PM (India time). The 4 AM run collects yesterday’s full day of sales; the 4 PM run collects today so far (roughly 8 AM to 4 PM) so the dashboard shows the day as it unfolds.',
        bullets: [
          'Windows Task Scheduler tasks: NutrioBox-DailyData-AM (4:00) and NutrioBox-DailyData-PM (16:00).',
          'It first re-logs into Petpooja so the data pull is authenticated (uses a saved login session).',
        ],
      },
      {
        title: '2. Download the raw orders from Petpooja',
        body:
          'A background Chrome browser opens Petpooja and exports the “Order Summary Item” report as a CSV file covering all 10 outlets for that day. It exports the file twice, about 3 minutes apart, and keeps the larger one — because some Zomato/Swiggy orders take a few minutes to appear, and we don’t want to miss them.',
        bullets: [
          'Where: billing.petpooja.com → Reports → Order Summary Item.',
          'Why twice: catches late-syncing online orders (a known gap that once cost ~₹900/day).',
        ],
      },
      {
        title: '3. Clean the data — one row per bill',
        body:
          'A single bill can have many item lines, so the totals would be over-counted if we left it as-is. We keep just one row per bill using the pair (outlet + invoice number) — exactly like using “Remove Duplicates on invoice number” in Excel. We keep Success and Cancelled bills; only Success bills count toward sales (Cancelled show as ₹0).',
        bullets: [
          'A full day is normally ~1,500–2,000 bills; a half-day (4 PM run) ~450–700.',
          'To reproduce in Excel: filter the CSV to the date, Remove Duplicates on invoice_no, sum the total column for Success rows.',
        ],
      },
      {
        title: '4. Add the add-on sales, outlet by outlet',
        body:
          'For each of the 10 outlets, the browser opens Petpooja’s “Addon: Item-Wise” report and reads how many add-ons were sold and their value. Each outlet’s figures are cross-checked against the report’s own “Total” row, so if a number is wrong the job stops rather than publishing bad data.',
        bullets: [
          'Outlets: DLF Phase 2, Rajinder Nagar, Dwarka, Janakpuri, Karkardooma, Noida, Prashant Vihar, Sector 15 Gurugram, Shivalik, Sector 63 Noida.',
          'Add-ons are stored separately so the dashboard can show them on their own.',
        ],
      },
      {
        title: '5. Safety cross-check (morning run only)',
        body:
          'On the 4 AM run, the day’s total sales from our export are compared with the grand total shown on Petpooja’s own dashboard. If our number is short by more than ₹200 (because some online orders settled late), it re-exports once to pick them up. This makes sure our number matches what management sees in Petpooja.',
      },
      {
        title: '6. Rebuild the dashboard’s data',
        body:
          'The cleaned bills and add-ons for the day are written into the dashboard’s data file. Any old rows for the same day are removed first, so re-running never creates duplicates. A safety check confirms the previous day’s total is completely unchanged — if it isn’t, the job aborts and publishes nothing.',
      },
      {
        title: '7. Publish to the website',
        body:
          'The rebuilt dashboard (about 100 MB) is compressed and uploaded to our storage (Supabase). The upload is then re-downloaded and its checksum compared, so we are certain the live website received exactly the right file.',
      },
      {
        title: '8. Live on the site',
        body:
          'operationsdashboard.nutriobox.com now shows the refreshed Sales Item Dashboard. It is reviewed around 10 AM (for the morning run) and in the evening (for the afternoon run).',
      },
    ],
  },

  'Discount Codes': {
    automated: true,
    tasks: ['daily-offer-tracker', 'nutriobox-discount-report-daily-upload'],
    schedule: 'Every day — report ~4:09 AM, site upload ~5:00 AM IST',
    intro:
      'This tracks which promotional offers / discount codes are live on Zomato and Swiggy for all 10 outlets, every day. It emails a report to management and also feeds the calendar view on this tile. Rule: it may only ever show today’s freshly-collected data — never yesterday’s.',
    steps: [
      {
        title: '1. The daily job starts (~4:09 AM)',
        body:
          'A scheduled job wakes up and prepares to collect the current day’s active offers. It clears any old data first so nothing stale can leak into today’s report.',
      },
      {
        title: '2. Read Zomato offers for all 10 outlets',
        body:
          'It calls Zomato’s partner “track-offers” service for each of the 10 restaurant IDs and lists every active offer, removing duplicates. Offers are split into two groups: “Standard” (codes NutrioBox itself configures) and “Extra” (added by Zomato).',
        bullets: [
          'Standard examples: flat ₹175 off above ₹449; flat ₹200 off above ₹999; 20% off above ₹800.',
          'Anything not in the Standard list is automatically “Extra”.',
        ],
      },
      {
        title: '3. Read Swiggy offers for all 10 outlets',
        body:
          'It makes one request to Swiggy’s data service that returns the active discount codes for all outlets at once, again split into Standard vs Extra.',
        bullets: ['Standard Swiggy codes: SAVEBITE, FREEDISH / BUY2GET1, PARTY, FLAT200, FLASHDEAL.'],
      },
      {
        title: '4. If Swiggy fails, retry — never send wrong data',
        body:
          'If Swiggy doesn’t respond cleanly, the job tries again after 5 minutes, then 10, then 15. If all four attempts fail, it sends a short “could not complete today” alert instead of a half-finished report. A late-but-correct report is preferred over a fast-but-wrong one.',
      },
      {
        title: '5. Build the report table',
        body:
          'It assembles an HTML table with one row per code, showing on how many of the 10 outlets that code is active (an n/10 count) and which outlets. Automatic quality checks run — for example, exactly 10 outlets must be present and the expected number of Standard rows must appear — or it will not send.',
      },
      {
        title: '6. Email the report',
        body:
          'The finished report is emailed to mayank@nutriobox.com through a Google Apps Script, which keeps the table formatting intact (normal email compose would break it).',
      },
      {
        title: '7. Publish to the dashboard (~5:00 AM)',
        body:
          'A second scheduled job fetches that email, wraps its contents in the site’s styling, and uploads it to storage as discount-codes-<date>.html so the tile can display it.',
      },
      {
        title: '8. Live on the tile',
        body:
          'The Discount Codes card shows a calendar. Picking any date opens that day’s saved offer report.',
      },
    ],
  },

  'Delay Dashboard': {
    automated: true,
    tasks: ['nutriobox-weekly-delay-dashboard'],
    schedule: 'Every Wednesday at 6:00 AM IST',
    intro:
      'This shows delivery-delay performance per outlet, one week at a time. Once a week it reads the latest completed week’s delay numbers from a Google Sheet and republishes the delay page.',
    steps: [
      {
        title: '1. The weekly job starts (Wednesday 6 AM)',
        body:
          'It works out the most recently completed Monday–Sunday week and the exact tab name for that week in the delay tracking Google Sheet.',
      },
      {
        title: '2. Read the delay numbers from the sheet',
        body:
          'It confirms that week’s tab actually exists (a required safety check), then reads the delay columns for all 10 outlets from that tab.',
      },
      {
        title: '3. Add the week to the dashboard file',
        body:
          'The new week’s numbers are appended to the delay dashboard’s data. Two identical copies of the file are kept in sync, and a checksum confirms they match before anything is published.',
      },
      {
        title: '4. Publish to the website',
        body:
          'The updated delay dashboard (a small file, uploaded uncompressed) is sent to storage. The live page picks it up within about a minute.',
      },
      {
        title: '5. Live on the site',
        body:
          'operationsdashboard.nutriobox.com/dashboard/delay now shows the new week alongside the earlier weeks.',
      },
    ],
  },

  'Customer Feedback': {
    automated: false,
    tasks: [],
    schedule: 'Internal page (no scheduled data job)',
    intro:
      'This is an internal page inside the Operations Dashboard app. There is no automated data pull behind it — the app serves the feedback and satisfaction content itself.',
    steps: [
      {
        title: '1. Served by the app',
        body:
          'Unlike the sales and KOT tiles, no scheduled job feeds this card. The page is part of the website and shows customer-feedback and satisfaction insights across outlets directly.',
      },
      {
        title: '2. Open the tile to view',
        body:
          'Clicking the card opens the internal feedback page. If you later want this to pull from a live source on a schedule, that automation would be added separately.',
      },
    ],
  },

  'Ratings': {
    automated: true,
    tasks: ['nutriobox-ratings-weekly-refresh'],
    schedule: 'Every Monday at ~8:07 AM IST',
    intro:
      'This refreshes each outlet’s star ratings and review counts on Zomato, Swiggy and Google, once a week, and publishes them to the Ratings tile with a trend over time.',
    steps: [
      {
        title: '1. The weekly job starts (Monday morning)',
        body:
          'It first loads the currently published ratings as a baseline. If any single source fails to load later, that outlet keeps its previous value — good data is never overwritten with a blank.',
      },
      {
        title: '2. Read ratings for each outlet on all 3 platforms',
        body:
          'For each of the 10 outlets, a browser reads the rating and review count from Google (the business panel), Zomato (the outlet page) and Swiggy (dine-out or delivery page).',
      },
      {
        title: '3. Save the ratings and the history',
        body:
          'It writes a ratings file (current values for all 10 outlets) and appends this week’s figures to a history file so the tile can draw a week-over-week trend chart.',
      },
      {
        title: '4. Live on the tile',
        body:
          'The Ratings card compares platforms per outlet and highlights which locations need attention. No website re-deploy is needed — the tile reads the saved files directly.',
      },
    ],
  },

  'Music Monitor': {
    automated: false,
    tasks: [],
    schedule: 'Live monitor (no scheduled data job)',
    intro:
      'This is a live view of what music is playing at each outlet right now. It reflects real-time device status rather than a once-a-day data pull.',
    steps: [
      {
        title: '1. Live device status',
        body:
          'For all 9 outlets it shows whether background music is playing on Bluetooth, on a laptop speaker, or not playing at all — broken down hour by hour.',
      },
      {
        title: '2. Open the tile to view',
        body: 'There is no scheduled job here; the card reflects the current state whenever you open it.',
      },
    ],
  },

  'Vehicle Monitoring Dashboard': {
    automated: false,
    tasks: [],
    schedule: 'Live GPS feed (no scheduled data job)',
    intro:
      'This tracks the delivery fleet live using the OneLap GPS feed. It updates in real time from GPS, so there is no daily or weekly job behind it.',
    steps: [
      {
        title: '1. Live GPS feed',
        body:
          'Each vehicle’s route, outlet stops, drive-vs-halt times and a full trip log per leg come straight from OneLap GPS in real time.',
      },
      {
        title: '2. Open the tile to view',
        body: 'The card shows the current fleet position and history whenever you open it — nothing is scheduled.',
      },
    ],
  },

  'Daily Dashboard': {
    automated: true,
    tasks: ['petpooja-sales-to-gsheet'],
    schedule: 'Every day at ~10:30 AM IST',
    intro:
      'This fills yesterday’s key sales numbers per outlet into the “Sales Data” Google Sheet. Opening the tile opens that sheet on the correct day’s tab.',
    steps: [
      {
        title: '1. The daily job starts (~10:30 AM)',
        body:
          'It works out yesterday’s date, which day-of-week tab to write to (Mon–Sun), and which row inside that tab is for yesterday’s date.',
      },
      {
        title: '2. Read yesterday’s sales from Petpooja',
        body:
          'It opens Petpooja’s POS dashboard, sets the date to yesterday, and reads the summary cards, the per-outlet sales table, and the Zomato/Swiggy split from the online-sales breakdown.',
      },
      {
        title: '3. Fill the Google Sheet',
        body:
          'It writes each outlet’s numbers into the day’s row (columns B–K are the 10 outlets), plus the total, net sales, percentage and average-order-value formulas (columns L, N, O, S, U). One screenshot is taken to verify the row looks right.',
        bullets: [
          'The 10 outlet totals must add up to the overall Total Sales as a check.',
          'Sheet: “Sales Data” — the tab named for yesterday’s weekday.',
        ],
      },
      {
        title: '4. Open from the tile',
        body: 'The Daily Dashboard card links straight to that day’s tab in the Google Sheet.',
      },
    ],
  },

  'Weekly Dashboard': {
    automated: true,
    tasks: [
      'weekly-petpooja-sales-report',
      'petpooja-weekly-sales-sync',
      'weekly-petpooja-dining-delivery-update',
    ],
    schedule: 'Wednesday 3:00 AM (main) + Monday jobs',
    intro:
      'This builds the full weekly sales picture in the “Weekly Sales” Google Sheet by combining data from Petpooja, Zomato and Swiggy for the last completed Monday–Sunday week. A few jobs fill different parts of the same sheet.',
    steps: [
      {
        title: '1. Main weekly entry starts (Wednesday 3 AM)',
        body:
          'It finds the last complete Monday–Sunday week, opens (or creates) that week’s tab, and clears the area it is about to fill so old numbers can’t linger.',
      },
      {
        title: '2. Pull orders & sales from Petpooja',
        body:
          'From Petpooja’s “Sub-Order Wise” report it fills the order counts, sales, and the dine-in vs online split, including the Zomato/Swiggy breakdown (columns D–S).',
      },
      {
        title: '3. Pull delivery-time (delay) data',
        body:
          'From Petpooja’s KOT delivery-time analysis it fills how many orders were delivered in 15–25 minutes and 26+ minutes, per outlet (columns T–W).',
      },
      {
        title: '4. Pull funnel data from Zomato & Swiggy',
        body:
          'It adds Zomato’s business funnel (impressions → menu → cart → orders, columns X–AH) and Swiggy’s business metrics from their downloaded report (columns AI–AR).',
      },
      {
        title: '5. Add Captain-App KOT and verify',
        body:
          'It brings the Captain-App KOT counts from the Weekly KOT sheet (columns AS–AU), then reads every cell back to confirm nothing was left blank — checking the sheet itself, not just the run log.',
      },
      {
        title: '6. Two smaller Monday jobs top it up',
        body:
          'On Monday, one job writes each outlet’s total sales from Petpooja’s All-Restaurant report, and another fills the month-to-date dining vs delivery percentages into the “Dining/Delivery” tab.',
      },
      {
        title: '7. Open from the tile',
        body: 'The Weekly Dashboard card opens last week’s tab in the Google Sheet.',
      },
    ],
  },

  'Daily KOT Comparison': {
    automated: true,
    tasks: ['daily-kot-comparison'],
    schedule: 'Every day at 5:10 AM IST',
    intro:
      'KOT means “Kitchen Order Ticket” — a ticket printed for each order. This compares the total KOTs (dine-in + pickup) against the KOTs raised through the Captain App, per outlet, for yesterday. It fills a Google Sheet and the tile always opens the newest day’s tab.',
    steps: [
      {
        title: '1. The daily job starts (5:10 AM)',
        body: 'It works out yesterday’s date and prepares to create a new tab named for that date.',
      },
      {
        title: '2. Count total KOTs from Petpooja',
        body:
          'On Petpooja’s KOT list it filters to Dine-In + Pickup order types for yesterday and reads the total KOT count for each of the 9 KOT outlets. This is column B.',
      },
      {
        title: '3. Count Captain-App KOTs',
        body:
          'On Petpooja’s Captain performance report it reads the “No of KOTs” total for each outlet. This is column C. (Column D and the totals are formulas in the sheet.)',
      },
      {
        title: '4. Write a new dated tab, then mirror it',
        body:
          'It creates a new tab (e.g. “16th August”) in the Daily KOT source sheet, fills in the numbers, then copies the same block into the “Daily KOT Comparison” tab of the main Sales Data sheet.',
      },
      {
        title: '5. Update the “latest tab” pointer',
        body:
          'The tile doesn’t hard-code which tab to open — it reads a small pointer file (kot-latest.json) that records the newest tab. That pointer is updated so the button always opens the freshest day.',
      },
      {
        title: '6. Open from the tile',
        body: 'The Daily KOT Comparison card opens the latest day’s tab automatically.',
      },
    ],
  },

  'Weekly KOT Comparison': {
    automated: true,
    tasks: ['kot-comparsion'],
    schedule: 'Every Monday at ~11:06 AM IST',
    intro:
      'The weekly version of the KOT comparison: total KOTs vs Captain-App KOTs per outlet, for the last completed Monday–Sunday week. It adds a new week tab and points the tile at it.',
    steps: [
      {
        title: '1. The weekly job starts (Monday)',
        body: 'It computes the last completed Monday–Sunday week (using a 1 PM–1 PM business-day window).',
      },
      {
        title: '2. Read KOT and Captain counts per outlet',
        body:
          'For each of the 9 outlets it reads the total KOT count (Dine-In + Pickup) and the Captain-App KOT count from Petpooja for that week.',
      },
      {
        title: '3. Create the week’s tab and fill it',
        body:
          'It duplicates the newest existing tab, renames it to the week range (e.g. “10th August – 16th August”), moves it to the front, and fills the KOT and Captain columns. It never deletes old tabs.',
      },
      {
        title: '4. Update the pointer & open from the tile',
        body:
          'The weekly pointer file (kot-weekly-latest.json) is updated to the new tab, so the Weekly KOT Comparison card always opens the latest week.',
      },
    ],
  },

  'Monthly KOT Comparison': {
    automated: true,
    tasks: ['monthly-kot-comparison'],
    schedule: 'On the 1st of each month at ~11:00 AM IST',
    intro:
      'The monthly version of the KOT comparison, in a separate sheet: total KOTs vs Captain-App KOTs per outlet, for the calendar month that just ended.',
    steps: [
      {
        title: '1. The monthly job starts (1st of month)',
        body: 'It works out the previous calendar month and the tab name for it (e.g. “July 2026”).',
      },
      {
        title: '2. Read KOT and Captain counts per outlet',
        body:
          'For each of the 9 outlets it reads the month’s total KOT count and Captain-App KOT count from Petpooja.',
      },
      {
        title: '3. Fill the month’s tab (safely re-runnable)',
        body:
          'If that month’s tab already exists it fills it in place; otherwise it creates one from a template. Either way, re-running never creates duplicates.',
      },
      {
        title: '4. Open from the tile',
        body: 'The Monthly KOT Comparison card opens the latest month’s tab.',
      },
    ],
  },

  'Momos Weekly Performance': {
    automated: true,
    tasks: ['nutriobox-momos-dashboard--weekly-update-higgsfield'],
    schedule: 'Every Monday at ~5:45 AM IST',
    intro:
      'This tracks momo sales specifically — units, revenue and veg vs non-veg mix across outlets, week by week. It reads Petpooja, computes the momo numbers, and updates a separate hosted dashboard app.',
    steps: [
      {
        title: '1. The weekly job starts (Monday)',
        body: 'It determines the last completed Monday–Sunday week and its end date.',
      },
      {
        title: '2. Export orders and keep only momos',
        body:
          'It exports Petpooja’s Order Summary report for all 10 outlets, drops exact duplicate rows, keeps Success orders, and filters to the 6 “Whole Wheat Momos” products.',
      },
      {
        title: '3. Compute the week’s momo numbers',
        body:
          'It classifies each item as veg or non-veg and by variant (Steamed / Tandoori / Chilli), then computes sales, units sold, orders and average order value per outlet.',
      },
      {
        title: '4. Update the Momos dashboard app',
        body:
          'It appends exactly one new week to the hosted Momos app’s data, updates the date labels, runs a sanity check (roughly ₹7 lakh expected — it stops if the number looks wrong), then commits and deploys.',
      },
      {
        title: '5. Open from the tile',
        body: 'The Momos Weekly Performance card links to the live app (nutriobox-momos.higgsfield.app).',
      },
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

/* ── Workflow modal — light theme, numbered step-by-step timeline ── */

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
        className="relative w-full max-w-2xl max-h-[88vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`h-1.5 w-full bg-gradient-to-r ${accent} rounded-t-2xl`} />

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 px-6 sm:px-8 pt-5 pb-4 bg-white/95 backdrop-blur border-b border-slate-100">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold text-slate-900">{label}</h2>
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                  flow.automated
                    ? 'text-emerald-700 bg-emerald-50 border-emerald-100'
                    : 'text-slate-500 bg-slate-50 border-slate-200'
                }`}
              >
                {flow.automated ? 'Automated' : 'Live / manual'}
              </span>
            </div>
            <div className="mt-1.5 flex items-center gap-1.5 text-[13px] font-medium text-brand-700">
              <ClockIcon />
              <span>{flow.schedule}</span>
            </div>
            {flow.tasks.length > 0 && (
              <div className="mt-1 text-[11px] text-slate-400 font-mono">
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

        {/* Body */}
        <div className="px-6 sm:px-8 py-6">
          {/* Plain-English overview */}
          <div className="mb-6 rounded-xl bg-slate-50 border border-slate-100 p-4">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400 mb-1">
              What this tile is
            </div>
            <p className="text-[14px] text-slate-700 leading-relaxed">{flow.intro}</p>
          </div>

          {/* Numbered step timeline */}
          <ol className="relative">
            {flow.steps.map((s, i) => {
              const isLast = i === flow.steps.length - 1;
              return (
                <li key={i} className="relative flex gap-4 pb-7 last:pb-0">
                  {/* connector rail */}
                  {!isLast && (
                    <span className="absolute left-[17px] top-9 bottom-0 w-0.5 bg-slate-200" aria-hidden="true" />
                  )}
                  {/* number bubble */}
                  <span
                    className={`relative z-10 shrink-0 flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br ${accent} text-white text-[14px] font-semibold shadow-sm`}
                  >
                    {i + 1}
                  </span>
                  {/* content */}
                  <div className="flex-1 pt-1">
                    <h3 className="text-[15px] font-semibold text-slate-900 leading-snug">
                      {s.title.replace(/^\d+\.\s*/, '')}
                    </h3>
                    <p className="mt-1.5 text-[14px] text-slate-600 leading-relaxed">{s.body}</p>
                    {s.bullets && s.bullets.length > 0 && (
                      <ul className="mt-2.5 space-y-1.5">
                        {s.bullets.map((b, j) => (
                          <li key={j} className="flex gap-2 text-[13px] text-slate-500 leading-relaxed">
                            <span className="mt-1.5 shrink-0 w-1.5 h-1.5 rounded-full bg-slate-300" />
                            <span>{b}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
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
