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

/* ── Workflow data (sourced from the Claude scheduled tasks that feed each tile) ── */

type WorkflowStep = {
  id: string;
  schedule: string;
  summary: string;
  steps: string[];
  sources: string;
  output: string;
  technical: string[];
};

type Workflow = {
  automated: boolean;
  note?: string;
  tasks: WorkflowStep[];
};

const WORKFLOWS: Record<string, Workflow> = {
  'Sales Item Dashboard': {
    automated: true,
    tasks: [
      {
        id: 'nutriobox-daily-data-v2',
        schedule: 'Twice daily — 4:00 AM & 4:00 PM IST',
        summary: 'Keeps the rolling sales dashboard current by pulling Petpooja order data twice a day and publishing it live.',
        steps: [
          'Compute the target date in IST (morning = yesterday full day; afternoon = today 8 AM–4 PM partial).',
          'Export the Order Summary Item CSV for all 10 outlets, double-exporting (3-min gap) to catch late Swiggy/Zomato orders.',
          'Dedupe rows to invoice level by (restaurant, invoice_no), keeping Success/Cancelled with total sales.',
          'Scrape the per-outlet Add-on report for all 10 outlets via one browser batch.',
          'Morning only: reconcile the export total against Petpooja’s POS Dashboard (₹200 threshold) and re-export once if short.',
          'Rebuild the ~100 MB dashboard’s DAILY_DATA, then gzip and upload to Supabase.',
        ],
        sources: 'Petpooja Order Summary Item CSV, Petpooja Add-on report (view_report/31), Petpooja POS Dashboard. No email.',
        output: 'Newest NutrioBox_Dashboard_*.html in Downloads\\NutrioBox_Reports, and Supabase reports/sales-dashboard.html (gzip) served here.',
        technical: [
          'Hard <100-turn budget; add-on scraping must use one browser batch (~10 turns, not 70).',
          'Phase-C filter keeps target-date rows before 08:00 and drops ≥08:00; prev-day stability delta must be 0 before writing.',
          'Supabase jkzremlkrxhhshqouudk; upload verified by gunzip md5 match against the local export.',
        ],
      },
      {
        id: 'nutriobox-monthly-dashboard',
        schedule: '1st of month, 11:15 AM IST (2nd if the 1st is a Sunday)',
        summary: 'Appends the previous full calendar month to the rolling Power BI-style HTML dashboard.',
        steps: [
          'Day-gate check; skip if not the 1st (or 2nd).',
          'Export the whole-month Order Summary Item CSV across all 10 outlets.',
          'Dedupe to invoice level, then aggregate by (restaurant, category, item, status).',
          'Scrape and aggregate the per-outlet Add-on report for the month.',
          'Merge into the dashboard’s DATA array, update MONTH_ORDER and the topbar title, save under a new filename.',
        ],
        sources: 'Petpooja Order Summary Item CSV + Petpooja Add-on report.',
        output: 'New NutrioBox_Dashboard_Sep2025_<MMMYYYY>.html in Downloads\\NutrioBox_Reports.',
        technical: [
          'Idempotent — drops existing rows for the month before re-appending.',
          'Only replaces DATA, MONTH_ORDER and the title; never touches page/CSS/JS structure.',
          'Sanity: ~30k–60k deduped invoices, sales ₹2 Cr+; monthly CSV ~20–50 MB.',
        ],
      },
    ],
  },

  'Discount Codes': {
    automated: true,
    tasks: [
      {
        id: 'daily-offer-tracker',
        schedule: 'Daily — 4:09 AM IST',
        summary: 'Scrapes current active promo offers for 10 outlets from Zomato and Swiggy and emails a formatted Offer Tracker report.',
        steps: [
          'Collect Zomato offers for all 10 res_ids via the merchant-api track-offers fetch, deduped by (title, minOrder).',
          'Collect Swiggy discounts via a single GraphQL POST for all 10 RIDs.',
          'Classify each offer into Standard Codes (NutrioBox-configured) vs Extra Codes (platform-added).',
          'Build one inline-CSS HTML email with Zomato and Swiggy tables, rows sorted by outlet count.',
          'Send via a Google Apps Script Web App and verify delivery in Gmail (3-retry chain on Swiggy failure).',
        ],
        sources: 'Zomato partner portal, Swiggy partner GraphQL (vhc-composer.swiggy.com), Swiggy access_token from localStorage.',
        output: 'HTML email to mayank@nutriobox.com (the upstream source for the site upload).',
        technical: [
          'Hard 100-turn cap; freshness policy locked — localStorage uses {runId, data} envelopes, no cross-run reuse.',
          'Swiggy Standard codes: SAVEBITE, FREEDISH/BUY2GET1, PARTY, FLAT200, FLASHDEAL.',
          '15 blocking quality checks (e.g. exactly 10 Swiggy RIDs) before send; never sends stale/partial data.',
        ],
      },
      {
        id: 'nutriobox-discount-report-daily-upload',
        schedule: 'Daily — 5:00 AM IST',
        summary: 'Fetches the latest Offer Tracker email and uploads today’s discount-codes report to Supabase for this tile.',
        steps: [
          'Load secrets from the Operationsdashboard .env.local and get a Gmail access token from the refresh token.',
          'Query the mailbox for from:"NutrioBox Offer Tracker" newer_than:1d and extract the HTML body.',
          'Wrap it in the standard style shell and PUT it to Supabase as discount-codes-YYYY-MM-DD.html (today, IST).',
          'Verify via /api/discount-codes-latest that latestDate equals today, then report.',
        ],
        sources: 'Gmail (mayank@nutriobox.com mailbox via Gmail API), secrets from .env.local.',
        output: 'Supabase reports/discount-codes-YYYY-MM-DD.html (the file this calendar tile serves).',
        technical: [
          'Remote job mirroring local fetch-discount-email.ps1 so it does not depend on laptop Task Scheduler.',
          'curl PUT with x-upsert:true, Cache-Control max-age=60.',
          'Failure branches: NO_EMAIL (tracker not arrived), token-refresh error, non-200 upload.',
        ],
      },
    ],
  },

  'Delay Dashboard': {
    automated: true,
    tasks: [
      {
        id: 'nutriobox-weekly-delay-dashboard',
        schedule: 'Wednesdays — 6:00 AM IST',
        summary: 'Appends the prior completed Mon–Sun week’s delivery-delay numbers and deploys the delay page.',
        steps: [
          'Determine the most recently completed Mon–Sun week and its tab name.',
          'Confirm the target tab exists (mandatory), then fetch it as CSV and pull columns T/U/V/W for the 10 outlets.',
          'Append the new week label and rows to weeks / data in both local HTML copies; update subtitle and heading.',
          'Verify file integrity (both copies md5-identical), then upload to Supabase reports/delay-dashboard.html.',
          'Confirm both the object and the /dashboard/delay route show the new week.',
        ],
        sources: 'Google Sheet gid=1322718967 (via local Chrome as satvik@nutriobox.com).',
        output: 'nutriobox_delay_dashboard_v3.html (two copies) + Supabase reports/delay-dashboard.html.',
        technical: [
          'Tab-existence check is mandatory — the gviz CSV endpoint silently falls back to the active sheet on a bad tab name.',
          'Delay dashboard is small (~18 KB) — uploaded plain, NO gzip (unlike sales).',
          '/api/delay-dashboard caches ~60s; strip commas and trailing .00 from numbers.',
        ],
      },
    ],
  },

  'Customer Feedback': {
    automated: false,
    note: 'No scheduled Claude task feeds this tile. It is an internal page inside the Operations Dashboard app that surfaces customer feedback and satisfaction insights across outlets. Content is served by the app itself rather than an automation, so there is no daily/weekly fetch job behind it.',
    tasks: [],
  },

  'Ratings': {
    automated: true,
    tasks: [
      {
        id: 'nutriobox-ratings-weekly-refresh',
        schedule: 'Mondays — 8:07 AM IST',
        summary: 'Refreshes each of the 10 outlets’ Zomato, Swiggy and Google ratings and review counts, published to the Ratings section.',
        steps: [
          'Fetch the current ratings.json as a baseline so failed sources keep their prior values.',
          'For each outlet read Google (knowledge panel), Zomato (JSON-LD aggregateRating) and Swiggy (dineout or delivery) ratings via Chrome.',
          'Build ratings.json with all 10 outlets in fixed order and exact names/cities.',
          'Upload ratings.json to Supabase reports/ratings.json.',
          'Append/replace this ISO week’s entry in ratings-history.json for the trend chart, then verify via /api/ratings.',
        ],
        sources: 'Google search knowledge panels, Zomato outlet pages, Swiggy dineout/delivery pages (logged-in Chrome).',
        output: 'Supabase reports/ratings.json and reports/ratings-history.json (surfaced via /api/ratings, 60s cache).',
        technical: [
          'Outlets 1–6 use Swiggy Dineout rating; outlets 7–10 (delivery-only) use Swiggy delivery rating.',
          'Data-only refresh — no code deploy / git push needed; the page reads the JSON directly.',
          'Google rating/count often render concatenated (e.g. "4.3517 reviews" = 4.3 / 517).',
        ],
      },
    ],
  },

  'Music Monitor': {
    automated: false,
    note: 'No scheduled Claude task feeds this tile. It is a live monitor showing the real-time background-music status for all 9 outlets — whether each is playing on Bluetooth, on a laptop speaker, or not playing at all — broken down hour by hour. The view reflects live device state rather than a batch fetch, so there is no scheduled automation behind it.',
    tasks: [],
  },

  'Vehicle Monitoring Dashboard': {
    automated: false,
    note: 'No scheduled Claude task feeds this tile. It is a live delivery-fleet view driven by the OneLap GPS feed — each vehicle’s route, outlet stops, drive vs halt times, and a full trip log per leg update in real time from GPS rather than from a daily/weekly job.',
    tasks: [],
  },

  'Daily Dashboard': {
    automated: true,
    tasks: [
      {
        id: 'petpooja-sales-to-gsheet',
        schedule: 'Daily — 10:30 AM IST',
        summary: 'Pulls the previous day’s Petpooja sales and fills the matching day-of-week tab of the Sales Data sheet.',
        steps: [
          'Compute yesterday’s date, weekday tab name, and day-of-month row label.',
          'On the Petpooja dashboard set the date range, switch to List view, and read the summary cards + per-outlet table.',
          'Open the Online Sales tooltip to capture the Zomato/Swiggy split.',
          'Open the Sales Data sheet, click the day-of-week tab, and anchor on column A to find the target row.',
          'Fill columns B–U in one batch (per-outlet totals + SUM/percent/AOV formulas) and verify with a screenshot.',
        ],
        sources: 'Petpooja POS dashboard (billing.petpooja.com/users/dashboard), all data via JS/DOM.',
        output: 'Google Sheet 1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs — the day-of-week tab, target date row.',
        technical: [
          'Column map B–K = 10 outlets (G = "Noida Advant" = NutrioBox Noida, K = "Sector 63 Noida" — do not swap).',
          'L=SUM, N=round(NetSales), O=N/L %, S=(L*0.95)/R AOV, U=100%−T (never hardcoded).',
          'Petpooja screenshots freeze from polling — on frozen renderer close and recreate the tab, never retry-wait.',
        ],
      },
    ],
  },

  'Weekly Dashboard': {
    automated: true,
    tasks: [
      {
        id: 'weekly-petpooja-sales-report',
        schedule: 'Wednesdays — 3:00 AM IST',
        summary: 'Full weekly (last Mon–Sun) sales entry — downloads PetPooja, Zomato and Swiggy reports and fills every column (D–AU).',
        steps: [
          'Compute last complete Mon–Sun week, open/create its tab, and clear D5:AU23.',
          'PetPooja Sub-Order Wise report → columns D–S (orders, sales, online/dine-in, platform split).',
          'PetPooja KOT Delivery Time Analysis → columns T–W (15–25 min and 26+ min delivery counts/%).',
          'Zomato funnel → columns X–AH; Swiggy business-metrics xlsx → columns AI–AR.',
          'Captain App KOT from the Weekly KOT sheet → columns AS–AU, then run a cell-level verify.',
        ],
        sources: 'PetPooja (Sub-Order Wise + KOT), Zomato Partner Dashboard, Swiggy business-metrics xlsx, Weekly KOT Comparison sheet.',
        output: 'Google Sheet 1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc — last-week tab, rows 5–23, columns D–AU.',
        technical: [
          'One self-verifying run() function that throws on blank; confirm against the SHEET, not the execution log.',
          'Sale = My Amount − Total Discount + Container Charge; Swiggy wizard selects both brands / 3 cities, deselects RID 43180.',
          'Row 9 (Noida 63) AS–AU stays blank (not in the KOT sheet); cross-check F=L+P and J=D−F.',
        ],
      },
      {
        id: 'petpooja-weekly-sales-sync',
        schedule: 'Mondays — 12:30 PM IST',
        summary: 'Writes last week’s per-outlet Total Sales from Petpooja’s All Restaurant Sales Report into the active Weekly tab.',
        steps: [
          'Open the All Restaurant Sales Report, set the Mon–Sun dates, All Outlets + Success, and search.',
          'Read per-outlet Total Sales and sanity-check that the 10 rounded totals sum to the report Total (±2).',
          'Compute the target column from the anchor (DA = Jan 5 2026) and confirm the row-2 day-of-month.',
          'Write each rounded outlet total, then the consolidated sum, and re-read 3 cells to verify.',
        ],
        sources: 'Petpooja All Restaurant Sales Report (custom_reports/view_report/9).',
        output: 'Google Sheet 1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs, gid=763903784 — outlet rows 7–43 + consolidated row 3.',
        technical: [
          'Moved to 12:30 (from 11:10) to avoid clobbering kot-comparsion’s Petpooja outlet session.',
          'Writes Total Sales (not Net Sales), rounded to integer; total sits in the 3rd of each outlet’s 3 rows.',
          'Stops and asks if the target cell is non-empty or the anchor/day-of-month mismatches.',
        ],
      },
      {
        id: 'weekly-petpooja-dining-delivery-update',
        schedule: 'Mondays — 8:00 AM IST',
        summary: 'Computes each outlet’s month-to-date delivery sale% and orders% from Petpooja and fills the "Dining/ Dlvry" tab.',
        steps: [
          'Set the date range from the 1st of the current month through yesterday.',
          'For each of 9 outlets switch outlet and read Total Sales, delivery sale/orders, and successful orders.',
          'Compute delivery sale% and orders% (2 decimals); capture the overall "% from Online" for the Nutriobox row.',
          'Write each outlet’s two percentages into the current month’s column pair, one cell at a time.',
        ],
        sources: 'Petpooja dashboard (billing.petpooja.com/users/dashboard).',
        output: 'Google Sheet 1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs, gid=35858929 ("Dining/ Dlvry") — rows 3–21, current-month column pair.',
        technical: [
          'Month column pairs mapped Jan F/G … Dec AB/AC — verify row 1 month before writing.',
          'Enter cells too fast and you get "70.73%%" — pause ~1s and spot-check the formula bar.',
          'Overall row 3 fills only the sale column; row 23 (Sec 63 Noida) is not filled.',
        ],
      },
    ],
  },

  'Daily KOT Comparison': {
    automated: true,
    tasks: [
      {
        id: 'daily-kot-comparison',
        schedule: 'Daily — 5:10 AM IST',
        summary: 'Pulls yesterday’s per-outlet Dine In/Pickup KOT and Captain App KOT into a new dated tab, then mirrors it into Sales Data.',
        steps: [
          'Compute yesterday and create a new "Dth Mmmm" tab in the source Daily KOT sheet.',
          'Column B: on the Petpooja KOT list set order type [Pickup, Dine In] + dates and read the records count per outlet.',
          'Column C: on the Captain report set the dates and read the Total row’s "No of Kots".',
          'Record all 9 outlet values, then fill the new source tab (D and TOTAL are formulas).',
          'Copy the same numbers into the matching date block of the Sales Data "Daily KOT Comparsion" tab.',
        ],
        sources: 'Petpooja KOT list (items/kot_list) and Captain App report (view_report/27).',
        output: 'Source sheet 1yOYpZBj…mn8 (new dated tab) + Sales Data 1r9u4DMs… "Daily KOT Comparsion" tab.',
        technical: [
          'Must finish within 80 tool calls; the newest tab is the leftmost (index 0) — the site’s pointer JSON tracks its gid.',
          'The morning health check republishes reports/kot-latest.json to this newest tab’s gid if the task skips it.',
          '9 outlet → row mappings fixed (DLF Phase 2 349767 = row 2 … Shivalik 62695 = row 10).',
        ],
      },
    ],
  },

  'Weekly KOT Comparison': {
    automated: true,
    tasks: [
      {
        id: 'kot-comparsion',
        schedule: 'Mondays — 11:06 AM IST',
        summary: 'Creates a new tab for the just-completed Mon–Sun week and fills Dine In/Pickup KOT (col B) and Captain App KOT (col C) for 9 outlets.',
        steps: [
          'Compute last Mon–Sun with a [Mon 13:00 → Mon 13:00) window.',
          'For each of 9 outlets switch restaurant and verify the selected id.',
          'Column B: on the KOT list set order type [Pickup, Dine In] + dates and read the records count.',
          'Column C: on the Captain report read the Total "No of Kots".',
          'Duplicate the leftmost (newest) tab, rename to the week range, move it leftmost, and fill B2:B10 / C2:C10.',
        ],
        sources: 'Petpooja KOT list (items/kot_list) and Captain App report (view_report/27).',
        output: 'Google Sheet 1eFBNV1b…QX30 — new week tab (e.g. "10th August - 16th August"), cols B/C.',
        technical: [
          'Sheet ordered newest-on-the-left; the site’s weekly pointer JSON tracks the newest tab’s gid.',
          'Never patch page JS (XHR/fetch/jQuery.ajax) — use in-page jQuery #kot_search submit; open a fresh tab if it hangs.',
          'Never delete a tab; note (not guess) any null/timeout cell.',
        ],
      },
    ],
  },

  'Monthly KOT Comparison': {
    automated: true,
    tasks: [
      {
        id: 'monthly-kot-comparison',
        schedule: '1st of month — 11:00 AM IST',
        summary: 'Creates/fills the previous calendar month’s tab in the Monthly KOT sheet with Dine In/Pickup KOT and Captain App KOT for 9 outlets.',
        steps: [
          'Compute the just-ended month with a [1st→1st) window and tab name (e.g. "July 2026").',
          'For each of 9 outlets switch restaurant and verify the selected id.',
          'Column B: on the KOT list set order type [Pickup, Dine In] + month dates and read the records count.',
          'Column C: on the Captain report read the Total "No of Kots".',
          'If the month tab exists, fill it; otherwise duplicate the leftmost tab, rename, and move leftmost — then verify.',
        ],
        sources: 'Petpooja KOT list (items/kot_list) and Captain App report (view_report/27).',
        output: 'Monthly KOT sheet 1TFCNxjX…Nofw — "<Month> <Year>" tab, cols B/C (D/TOTAL auto).',
        technical: [
          'Separate sheet from the weekly kot-comparsion task; idempotent on the month tab.',
          'Shares the Petpooja login with ~10:30 and ~11:15 jobs — verify selected_restaurant_id before every read.',
          'Same JS-safety and ref-based Google Sheets rules; fill each cell separately (type inserts literal tabs).',
        ],
      },
    ],
  },

  'Momos Weekly Performance': {
    automated: true,
    tasks: [
      {
        id: 'nutriobox-momos-dashboard--weekly-update-higgsfield',
        schedule: 'Mondays — 5:45 AM IST',
        summary: 'Appends the just-completed week’s momo performance (from Petpooja) to the Higgsfield "nutriobox-momos" app and redeploys it.',
        steps: [
          'Determine the previous Mon–Sun week and its Sunday end date.',
          'Export the Petpooja Order Summary Item CSV for all 10 outlets (excluding the Test ID).',
          'Drop duplicate rows, keep Success, filter "Whole Wheat Momos" (6 SKUs), classify veg/nonveg + variant; compute sales/units/orders per outlet.',
          'Clone the Higgsfield repo and append exactly ONE week to the const D data block and cumulative KPIs.',
          'Update the 4 date-label spots, sanity-check (~₹7L expected), commit, push, deploy, and verify the live URL.',
        ],
        sources: 'Petpooja Order Summary Item report (reports/order_summary_item) via Windows Chrome.',
        output: 'Higgsfield app "nutriobox-momos" (nutriobox-momos.higgsfield.app), linked from this Momos card.',
        technical: [
          'Edits the const D block only; keeps Weeks 1–8+ history and the "1 Jun" start unchanged; aov = round(sales/orders).',
          'Veg rule: item starting with "Chicken" → Nonveg, else Veg.',
          'Does NOT edit the Operations website repo; hard-reloads the live URL with a cache-buster (CDN ~30s).',
        ],
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

/* ── Workflow modal ── */

function WorkflowModal({
  label,
  accent,
  onClose,
}: {
  label: string;
  accent: string;
  onClose: () => void;
}) {
  const wf = WORKFLOWS[label];
  if (!wf) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-[fadeIn_0.15s_ease-out]"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${label} workflow`}
    >
      <div
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`h-1.5 w-full bg-gradient-to-r ${accent} rounded-t-2xl`} />

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start justify-between gap-4 px-6 pt-5 pb-4 bg-white/95 backdrop-blur border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-slate-900">{label}</h2>
              <span
                className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full border ${
                  wf.automated
                    ? 'text-emerald-700 bg-emerald-50 border-emerald-100'
                    : 'text-slate-500 bg-slate-50 border-slate-200'
                }`}
              >
                {wf.automated ? 'Automated' : 'Live / manual'}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-slate-400">
              {wf.automated
                ? 'Kept up to date by scheduled Claude tasks — here is exactly what runs.'
                : 'How this tile stays current.'}
            </p>
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
        <div className="px-6 py-5 space-y-6">
          {!wf.automated && wf.note && (
            <p className="text-sm text-slate-600 leading-relaxed">{wf.note}</p>
          )}

          {wf.tasks.map((task, ti) => (
            <div key={task.id} className={ti > 0 ? 'pt-6 border-t border-slate-100' : ''}>
              {/* Task header */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-brand-700 bg-brand-50 px-2.5 py-1 rounded-full border border-brand-100">
                  <ClockIcon />
                  {task.schedule}
                </span>
                <code className="text-[11px] text-slate-400 font-mono">{task.id}</code>
              </div>

              <p className="mt-3 text-sm text-slate-700 leading-relaxed">{task.summary}</p>

              {/* Steps */}
              <div className="mt-4">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">How it works</h3>
                <ol className="mt-2 space-y-2">
                  {task.steps.map((s, i) => (
                    <li key={i} className="flex gap-3 text-sm text-slate-600">
                      <span className="shrink-0 flex items-center justify-center w-5 h-5 mt-0.5 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-500">
                        {i + 1}
                      </span>
                      <span className="leading-relaxed">{s}</span>
                    </li>
                  ))}
                </ol>
              </div>

              {/* Sources / Output */}
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Pulls from</div>
                  <div className="mt-1 text-xs text-slate-600 leading-relaxed">{task.sources}</div>
                </div>
                <div className="rounded-lg bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Lands in</div>
                  <div className="mt-1 text-xs text-slate-600 leading-relaxed">{task.output}</div>
                </div>
              </div>

              {/* Technical details */}
              <details className="mt-3 group">
                <summary className="cursor-pointer list-none flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 transition-colors">
                  <span className="transition-transform group-open:rotate-90">
                    <ChevronRight />
                  </span>
                  Technical details
                </summary>
                <ul className="mt-2 ml-1 space-y-1.5">
                  {task.technical.map((t, i) => (
                    <li key={i} className="flex gap-2 text-xs text-slate-500 leading-relaxed">
                      <span className="text-slate-300">•</span>
                      <span>{t}</span>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          ))}
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

          const hasWorkflow = card.label in WORKFLOWS;

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
