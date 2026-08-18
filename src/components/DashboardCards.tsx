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

function DownArrow() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
      <path d="M12 5v14M6 13l6 6 6-6" />
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

/* ── Workflow algorithm diagrams (built from each tile's Claude scheduled task).
   Rendered as a top-to-bottom flowchart: each box is a stage with detail lines
   and optional ├── branches, joined by a labelled ▼ arrow to the next box. */

type FlowNode = {
  stage: string;
  detail?: string[];
  branches?: string[];
  edge?: string;
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
    tasks: ['nutriobox-daily-data-v2 (Playwright automation)'],
    schedule: 'Every day at 4:00 AM & 4:00 PM IST',
    nodes: [
      { stage: 'WINDOWS TASK SCHEDULER (office laptop)',
        detail: ['Runs automatically twice a day.', '4:00 AM → yesterday, full day', '4:00 PM → today so far (8 AM–4 PM)'],
        edge: 'first re-logs into Petpooja (saved session)' },
      { stage: 'DOWNLOAD ORDERS FROM PETPOOJA',
        detail: ['Background Chrome opens the “Order Summary Item” report', 'Exports a CSV for all 10 outlets', 'Exports twice (~3 min apart) and keeps the larger file'],
        edge: 'twice = catch late Zomato/Swiggy orders' },
      { stage: 'CLEAN → ONE ROW PER BILL',
        detail: ['Keep one row per (outlet + invoice no) — like Excel “Remove Duplicates”', 'Keep Success + Cancelled; only Success counts as sales', 'Full day ≈ 1,500–2,000 bills; half day ≈ 450–700'],
        edge: '' },
      { stage: 'ADD-ON SALES — “Addon: Item-Wise” report',
        detail: ['Opens the add-on report for each outlet and reads qty + value', 'Each outlet is verified against the report’s own Total row'],
        branches: ['DLF Phase 2 · Rajinder Nagar', 'Dwarka · Janakpuri · Karkardooma', 'Noida · Prashant Vihar · Shivalik', 'Sector 15 Gurugram · Sector 63 Noida'],
        edge: '' },
      { stage: 'MORNING CROSS-CHECK (4 AM run only)',
        detail: ['Compare our day total vs Petpooja’s own dashboard total', 'Re-export once if we are short by more than ₹200'],
        edge: '' },
      { stage: 'REBUILD DASHBOARD DATA',
        detail: ['Write the day’s bills + add-ons into the data file', 'Remove old rows for the same day first (no duplicates)', 'Safety: previous day’s total must be unchanged, or STOP'],
        edge: '' },
      { stage: 'PUBLISH TO WEBSITE',
        detail: ['Compress (~100 MB → ~8 MB) and upload to storage (Supabase)', 'Re-download and compare a checksum to confirm the right file'],
        edge: '' },
      { stage: 'LIVE — operationsdashboard.nutriobox.com',
        detail: ['Reviewed ~10 AM (morning run) and evening (afternoon run)'] },
    ],
  },

  'Discount Codes': {
    automated: true,
    tasks: ['daily-offer-tracker', 'nutriobox-discount-report-daily-upload'],
    schedule: 'Every day — report ~4:09 AM, site upload ~5:00 AM IST',
    nodes: [
      { stage: 'DAILY JOB STARTS (~4:09 AM)',
        detail: ['Clears yesterday’s data first', 'Rule: only today’s freshly-collected data may be sent'],
        edge: '' },
      { stage: 'ZOMATO OFFERS — all 10 outlets',
        detail: ['Calls Zomato’s partner “track-offers” for each restaurant ID', 'De-duplicates, then splits Standard vs Extra'],
        branches: ['Standard: ₹175/₹449 · ₹200/₹999 · 20%/₹800', 'Extra: everything else Zomato added'],
        edge: '' },
      { stage: 'SWIGGY OFFERS — all 10 outlets',
        detail: ['One request returns every outlet’s active codes at once', 'Splits Standard vs Extra'],
        branches: ['Standard: SAVEBITE · FREEDISH/BUY2GET1 · PARTY · FLAT200 · FLASHDEAL'],
        edge: 'if Swiggy fails →' },
      { stage: 'RETRY IF SWIGGY FAILS',
        detail: ['Retries after 5, then 10, then 15 minutes', 'If all 4 attempts fail → send a short “could not complete” alert', 'Never sends partial or stale data'],
        edge: 'on success →' },
      { stage: 'BUILD THE REPORT TABLE',
        detail: ['One row per code, with an n/10 outlet-coverage count', 'Quality checks: exactly 10 outlets, expected number of Standard rows'],
        edge: '' },
      { stage: 'EMAIL THE REPORT',
        detail: ['Sent to mayank@nutriobox.com via a Google Apps Script', 'Apps Script keeps the table formatting intact'],
        edge: '' },
      { stage: 'UPLOAD TO THE SITE (~5:00 AM)',
        detail: ['A second job fetches that email', 'Wraps it in site styling → discount-codes-<date>.html on Supabase'],
        edge: '' },
      { stage: 'LIVE — Discount Codes tile',
        detail: ['Calendar view: pick any date to open that day’s report'] },
    ],
  },

  'Delay Dashboard': {
    automated: true,
    tasks: ['nutriobox-weekly-delay-dashboard'],
    schedule: 'Every Wednesday at 6:00 AM IST',
    nodes: [
      { stage: 'WEEKLY JOB STARTS (Wed 6 AM)',
        detail: ['Works out the last completed Mon–Sun week and its sheet tab name'],
        edge: '' },
      { stage: 'READ THE DELAY GOOGLE SHEET',
        detail: ['Confirms that week’s tab actually exists (mandatory check)', 'Reads the delay columns (T / U / V / W) for all 10 outlets'],
        edge: '' },
      { stage: 'APPEND THE WEEK',
        detail: ['Adds the new week to the delay dashboard file', 'Two identical copies kept in sync (checksum must match)'],
        edge: '' },
      { stage: 'PUBLISH',
        detail: ['Uploads to storage (small file, no compression)'],
        edge: '' },
      { stage: 'LIVE — /dashboard/delay',
        detail: ['New week appears within about a minute'] },
    ],
  },

  'Customer Feedback': {
    automated: false,
    tasks: [],
    schedule: 'Internal page (no scheduled data job)',
    nodes: [
      { stage: 'INTERNAL PAGE',
        detail: ['No scheduled data job feeds this tile', 'The content is served by the website itself'],
        edge: '' },
      { stage: 'CUSTOMER FEEDBACK TILE',
        detail: ['Feedback and satisfaction insights across outlets'] },
    ],
  },

  'Ratings': {
    automated: true,
    tasks: ['nutriobox-ratings-weekly-refresh'],
    schedule: 'Every Monday at ~8:07 AM IST',
    nodes: [
      { stage: 'WEEKLY JOB STARTS (Mon 8:07 AM)',
        detail: ['Loads the current ratings as a baseline', 'If a source fails later, that outlet keeps its previous value (never blanked)'],
        edge: '' },
      { stage: 'READ 3 PLATFORMS PER OUTLET (×10)',
        detail: ['For each outlet, read the star rating + review count'],
        branches: ['Google — business panel', 'Zomato — outlet page', 'Swiggy — dine-out / delivery page'],
        edge: '' },
      { stage: 'SAVE RATINGS + HISTORY',
        detail: ['Writes ratings.json (current values)', 'Appends this week to a history file for the trend chart'],
        edge: '' },
      { stage: 'LIVE — Ratings tile',
        detail: ['Compare platforms per outlet; spot ones needing attention', 'No site re-deploy — the tile reads the files directly'] },
    ],
  },

  'Music Monitor': {
    automated: false,
    tasks: [],
    schedule: 'Live monitor (no scheduled data job)',
    nodes: [
      { stage: 'LIVE MONITOR',
        detail: ['No scheduled job — reflects real-time device state', 'All 9 outlets, broken down hour by hour'],
        edge: '' },
      { stage: 'MUSIC MONITOR TILE',
        detail: ['Shows Bluetooth / laptop speaker / not playing'] },
    ],
  },

  'Vehicle Monitoring Dashboard': {
    automated: true,
    tasks: ['vehicle_report.py (Windows Task Scheduler)'],
    schedule: 'Every evening (~7–8 PM IST)',
    nodes: [
      { stage: 'EVENING JOB STARTS (~7–8 PM)',
        detail: ['A scheduled job runs on the office laptop each evening, after routes finish.', 'It logs into OneLap — the GPS system fitted in the delivery vehicles.'],
        edge: '' },
      { stage: 'GET EACH VEHICLE’S TRIPS FROM ONELAP',
        detail: ['Reads every vehicle’s trips for the day — start/end times, distance and GPS points.', 'Vehicles that drove less than 5 km are skipped as “no run”.'],
        edge: '' },
      { stage: 'WORK OUT THE STOPS',
        detail: ['Finds where a vehicle stood still for 15+ minutes — a delivery stop.', 'If a stop is within ~1.8 km of a NutrioBox outlet, it’s named as that outlet; otherwise the locality name is looked up from the map.'],
        branches: ['Depot = NutrioBox Noida 63', '9 outlets on the map (Shivalik, DLF Phase 2, Dwarka, …)'],
        edge: '' },
      { stage: 'BUILD THE REPORT',
        detail: ['Works out each leg: which outlet, drive time, halt time, and checkpoints at 30/60/90/120 min.', 'Produces the dashboard data plus an Excel report — one sheet per vehicle.'],
        edge: '' },
      { stage: 'PUBLISH + EMAIL',
        detail: ['Updates the Vehicle Monitoring tile on the website.', 'Emails the Excel report to satvik@nutriobox.com.'],
        edge: '' },
      { stage: 'LIVE — Vehicle Monitoring tile',
        detail: ['A date filter shows each day’s vehicles, routes, stops, and full trip log.'] },
    ],
  },

  'Daily Dashboard': {
    automated: true,
    tasks: ['petpooja-sales-to-gsheet'],
    schedule: 'Every day at ~10:30 AM IST',
    nodes: [
      { stage: 'DAILY JOB STARTS (~10:30 AM)',
        detail: ['Works out yesterday’s date, the weekday tab, and the target row'],
        edge: '' },
      { stage: 'READ PETPOOJA POS (yesterday)',
        detail: ['Reads the summary cards and per-outlet sales table', 'Opens the online-sales tooltip for the Zomato / Swiggy split'],
        edge: '' },
      { stage: 'FILL THE “SALES DATA” SHEET',
        detail: ['Writes into the day-of-week tab, yesterday’s row'],
        branches: ['B–K = the 10 outlet totals', 'L = SUM · N = Net Sales', 'O / S / U = % and average-order-value formulas'],
        edge: 'check: 10 outlet totals must equal overall Total Sales' },
      { stage: 'LIVE — opens the Google Sheet',
        detail: ['The Daily Dashboard card links to that day’s tab'] },
    ],
  },

  'Weekly Dashboard': {
    automated: true,
    tasks: ['weekly-petpooja-sales-report', 'petpooja-weekly-sales-sync', 'weekly-petpooja-dining-delivery-update'],
    schedule: 'Wednesday 3:00 AM (main) + Monday jobs',
    nodes: [
      { stage: 'MAIN WEEKLY JOB (Wed 3 AM)',
        detail: ['Finds the last complete Mon–Sun week', 'Opens/creates its tab and clears the area it will fill'],
        edge: '' },
      { stage: 'PETPOOJA — SUB-ORDER WISE REPORT',
        detail: ['Order counts, sales, dine-in vs online, Zomato/Swiggy split'],
        edge: '→ columns D–S' },
      { stage: 'PETPOOJA — KOT DELIVERY-TIME',
        detail: ['Orders delivered in 15–25 min and 26+ min, per outlet'],
        edge: '→ columns T–W' },
      { stage: 'ZOMATO + SWIGGY FUNNELS',
        detail: ['Zomato funnel: impressions → menu → cart → orders', 'Swiggy business metrics from its downloaded report'],
        edge: '→ X–AH · AI–AR' },
      { stage: 'CAPTAIN-APP KOT + VERIFY',
        detail: ['Brings Captain-App KOT from the Weekly KOT sheet', 'Reads every cell back — stops if any is left blank'],
        edge: '→ AS–AU' },
      { stage: 'MONDAY TOP-UP JOBS',
        detail: ['Mon 12:30 — total sales per outlet', 'Mon 08:00 — dining vs delivery %'],
        edge: '' },
      { stage: 'LIVE — opens the Google Sheet',
        detail: ['The Weekly Dashboard card opens last week’s tab'] },
    ],
  },

  'Daily KOT Comparison': {
    automated: true,
    tasks: ['daily-kot-comparison'],
    schedule: 'Every day at 5:10 AM IST',
    nodes: [
      { stage: 'DAILY JOB STARTS (5:10 AM)',
        detail: ['KOT = Kitchen Order Ticket (one per order)', 'Compares total KOTs vs Captain-App KOTs, per outlet', 'Target = yesterday'],
        edge: '' },
      { stage: 'COUNT TOTAL KOTs — PETPOOJA',
        detail: ['KOT list filtered to Dine-In + Pickup for yesterday', 'Reads the count for each of the 9 KOT outlets'],
        edge: '→ column B' },
      { stage: 'COUNT CAPTAIN-APP KOTs',
        detail: ['Captain performance report → the “No of KOTs” total'],
        edge: '→ column C (col D + totals are formulas)' },
      { stage: 'WRITE A NEW DATED TAB',
        detail: ['New tab, e.g. “16th August”, in the source KOT sheet', 'Mirror the same block into the Sales Data “Daily KOT Comparison” tab'],
        edge: '' },
      { stage: 'UPDATE THE “LATEST TAB” POINTER',
        detail: ['The tile reads kot-latest.json to know the newest tab', 'Pointer updated so the button always opens the freshest day'],
        edge: '' },
      { stage: 'LIVE — Daily KOT tile',
        detail: ['Opens the latest day’s tab automatically'] },
    ],
  },

  'Weekly KOT Comparison': {
    automated: true,
    tasks: ['kot-comparsion'],
    schedule: 'Every Monday at ~11:06 AM IST',
    nodes: [
      { stage: 'WEEKLY JOB STARTS (Mon 11:06 AM)',
        detail: ['Computes the last completed Mon–Sun week (1 PM–1 PM window)'],
        edge: '' },
      { stage: 'READ KOT + CAPTAIN (9 outlets)',
        detail: ['Total KOTs (Dine-In + Pickup) and Captain-App KOTs for the week'],
        edge: '' },
      { stage: 'CREATE THE WEEK’S TAB',
        detail: ['Duplicate the newest tab → rename “10th Aug – 16th Aug” → move to front', 'Fill KOT + Captain columns; old tabs are never deleted'],
        edge: '' },
      { stage: 'UPDATE POINTER → LIVE',
        detail: ['kot-weekly-latest.json points to the new tab', 'Weekly KOT tile opens the latest week'] },
    ],
  },

  'Monthly KOT Comparison': {
    automated: true,
    tasks: ['monthly-kot-comparison'],
    schedule: 'On the 1st of each month at ~11:00 AM IST',
    nodes: [
      { stage: 'MONTHLY JOB STARTS (1st, 11:00 AM)',
        detail: ['Works out the previous calendar month and tab name (e.g. “July 2026”)'],
        edge: '' },
      { stage: 'READ KOT + CAPTAIN (9 outlets)',
        detail: ['The month’s total KOTs and Captain-App KOTs'],
        edge: '' },
      { stage: 'FILL THE MONTH TAB (re-runnable)',
        detail: ['If the month tab exists, fill it; otherwise create from a template', 'Re-running never creates duplicates'],
        edge: '' },
      { stage: 'LIVE — Monthly KOT tile',
        detail: ['Opens the latest month’s tab'] },
    ],
  },

  'Momos Weekly Performance': {
    automated: true,
    tasks: ['nutriobox-momos-dashboard--weekly-update-higgsfield'],
    schedule: 'Every Monday at ~5:45 AM IST',
    nodes: [
      { stage: 'WEEKLY JOB STARTS (Mon 5:45 AM)',
        detail: ['Determines the last completed Mon–Sun week'],
        edge: '' },
      { stage: 'EXPORT ORDERS → KEEP ONLY MOMOS',
        detail: ['Petpooja Order Summary for all 10 outlets', 'Drop duplicates, keep Success, filter the 6 Whole Wheat Momos products'],
        edge: '' },
      { stage: 'COMPUTE THE WEEK',
        detail: ['Sales, units sold, orders and average order value per outlet'],
        branches: ['Veg vs Non-veg', 'Steamed / Tandoori / Chilli'],
        edge: '' },
      { stage: 'UPDATE THE MOMOS APP',
        detail: ['Append exactly one new week to the hosted app data', 'Sanity check ~₹7 lakh (stops if it looks wrong) → commit → deploy'],
        edge: '' },
      { stage: 'LIVE — nutriobox-momos.higgsfield.app',
        detail: ['The Momos Weekly Performance card links to it'] },
    ],
  },
};

/* ── Technical architecture diagrams (developer view) — real endpoints,
   scripts, data structures, storage paths, cron and serving routes. ── */

const TECH: Record<string, { stack?: string; nodes: FlowNode[] }> = {
  'Sales Item Dashboard': {
    stack: 'Windows Task Scheduler · Playwright · Python 3.14 · requests/bs4 · Supabase Storage · Next.js/Vercel',
    nodes: [
      { stage: 'TRIGGER — Windows Task Scheduler',
        detail: ['Tasks NutrioBox-DailyData-AM (04:00) / -PM (16:00), IST', 'Runs automation\\run_daily.bat → refresh_tokens.py → daily_data.py', 'Run mode: IST hour<12 ⇒ yesterday full day, else today partial'],
        edge: 'formerly Cowork task nutriobox-daily-data-v2' },
      { stage: 'AUTH — refresh_tokens.py',
        detail: ['Playwright persistent context (secrets/browser-profile)', 'Harvests cookies → secrets/tokens.json', 'petpooja.Petpooja.from_tokens() attaches cookie to a requests.Session'],
        edge: '' },
      { stage: 'EXPORT — browser_export.py (Playwright)',
        detail: ['GET billing.petpooja.com/reports/order_summary_item', 'JS sets data[Order][startdate|enddate] + selects 10 outlets (excl 399785)', 'Click Export → read S3 <a href> → download CSV', 'Double export, NBDD_EXPORT_SLEEP=180s; larger row count wins'],
        edge: '' },
      { stage: 'DEDUPE — daily_data.dedupe_csv()',
        detail: ['csv.DictReader; keep status in {Success, Cancelled}; drop rows containing "Test"', 'key = (restaurant_name, invoice_no), first row kept (= Excel “Remove Duplicates on invoice_no”)', 'record{qty,date,time,totalSales(Success only, else 0),status,invoiceNo,orderType,paymentType,area}', 'afternoon run: also drop date==target && time<08:00 (belongs to prior biz day)'],
        branches: ['QUIRK: restaurant_name has odd spaces — kept verbatim:', '  "NutrioBox ( DLF Phase 2)" · "NutrioBox ( Rajinder Nagar)"', '  "NutrioBox ( Sector 63 Noida )" (spaces inside the brackets)'],
        edge: '' },
      { stage: 'ADD-ONS — browser_export.scrape_addons()',
        detail: ['Report 31 is JS-rendered ⇒ Playwright, not HTTP', 'switch outlet: POST / (header_changed_rest_id)', 'GET custom_reports/view_report/31 → set re_filter_filed_1_23_* → Search', 'scrape #re_pivot_table_1; verify sums vs Total row; 10× config.OUTLETS'],
        edge: '' },
      { stage: 'RECONCILE — pos_dashboard_total() (morning only)',
        detail: ['GET billing.petpooja.com/users/dashboard → parse the All-Outlet Total Sales', 'threshold ₹200: if export_total < pos_total − 200 ⇒ one extra export, keep the CSV closest to POS', '⚠ KNOWN BUG: the parser sometimes reads a wrong small number (e.g. ₹1,050 on 18 Aug), so the check no-ops — fix pending'],
        edge: '' },
      { stage: 'REBUILD — dashboard_build.rebuild()',
        detail: ['Byte-slice ~135MB HTML at marker "const DAILY_DATA=" — exactly 17 chars (NOT 18)', 'QUIRK: prefix must end b"=[" (never "=[{") and the file must end </html>, else abort', 'drop target biz-day (time≥08:00) + next-day <01:00; KEEP target-date <08:00 tail', 'append; prev-day biz sales delta MUST == 0 else abort (guards against over-delete)', 'write once → NutrioBox_Reports\\NutrioBox_Dashboard_*.html'],
        edge: '' },
      { stage: 'PUBLISH — dashboard_build.publish()',
        detail: ['gzip -9 → POST Supabase /storage/v1/object/reports/sales-dashboard.html', 'headers: apikey + Bearer SERVICE_ROLE_KEY, Content-Encoding: gzip, x-upsert', 'verify: re-download (cache-bust) → gunzip → md5 == local (retry ×4)'],
        edge: '' },
      { stage: 'SERVE — Next.js on Vercel',
        detail: ['/api/sales-dashboard proxies the gzip object', 'iframe at /dashboard/sales-item; Supabase project jkzremlkrxhhshqouudk', 'claude_assist.py = env-gated fallback (ANTHROPIC_API_KEY), off by default'] },
    ],
  },

  'Discount Codes': {
    stack: 'Cowork task (cron) · Zomato REST · Swiggy GraphQL · Google Apps Script · Gmail API · Supabase · Next.js',
    nodes: [
      { stage: 'TRIGGERS — Cowork tasks',
        detail: ['daily-offer-tracker: cron 0 4 * * * (~4:09 IST)', 'nutriobox-discount-report-daily-upload: cron 0 5 * * *', 'Mailbox: mayank@nutriobox.com'],
        edge: '' },
      { stage: 'ZOMATO — REST fetch',
        detail: ['GET www.zomato.com/merchant-api/growth/offers/track-offers?res_id=&status=active', 'credentials:include; parse ratecard_list; dedupe (title,minOrder)', 'classify Standard vs Extra by title/minOrder patterns'],
        edge: '' },
      { stage: 'SWIGGY — GraphQL POST',
        detail: ['POST vhc-composer.swiggy.com/query', 'header access_token from partner.swiggy.com localStorage', 'ssdSubscriptionDetails(restaurantIds:[…] status:["ACTIVE"])', 'no credentials:include (avoids CORS preflight)'],
        edge: 'on fail: one-shot retry tasks +5/+10/+15 min' },
      { stage: 'BUILD — inline-CSS HTML',
        detail: ['one row per code = union of RIDs; n/10 column', 'localStorage {runId,data} envelopes (no cross-run reuse)', '15 blocking QA checks (10 RIDs, band counts)'],
        edge: '' },
      { stage: 'SEND — Apps Script Web App',
        detail: ['POST script.google.com/.../exec  mode:no-cors, text/plain', 'GmailApp.sendEmail preserves HTML (thread prefix Ktbx)'],
        edge: '' },
      { stage: 'UPLOAD — discount report job',
        detail: ['Gmail API (refresh token) from:"NutrioBox Offer Tracker" newer_than:1d', 'wrap HTML → PUT Supabase reports/discount-codes-YYYY-MM-DD.html (x-upsert)'],
        edge: '' },
      { stage: 'SERVE — Next.js',
        detail: ['/api/discount-codes-report?date= and /api/discount-codes-latest', 'calendar picker at /dashboard/discount-codes'] },
    ],
  },

  'Delay Dashboard': {
    stack: 'Cowork task · Google Sheets gviz CSV · HTML data-array edit · Supabase · Next.js',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['nutriobox-weekly-delay-dashboard, cron 0 6 * * 3 (Wed 6 AM)'],
        edge: '' },
      { stage: 'READ — Google Sheet (gviz)',
        detail: ['Sheet 1oNCCGX…G0qpc, gid=1322718967', 'gviz/tq?tqx=out:csv (auth via local Chrome, satvik@)', 'cols T/U/V/W for 10 outlets; mandatory tab-existence check'],
        edge: '' },
      { stage: 'BUILD — edit HTML data arrays',
        detail: ['append week to const weeks / const data', 'two copies (NutrioBox_Reports + Application), md5-identical'],
        edge: '' },
      { stage: 'PUBLISH — Supabase',
        detail: ['POST reports/delay-dashboard.html (plain text, NO gzip — ~18KB)'],
        edge: '' },
      { stage: 'SERVE — Next.js',
        detail: ['/api/delay-dashboard (≈60s cache) → /dashboard/delay'] },
    ],
  },

  'Customer Feedback': {
    stack: 'Next.js route (no job)',
    nodes: [
      { stage: 'STATIC / INTERNAL PAGE',
        detail: ['Next.js route /dashboard/feedback', 'No scheduled job, no external fetch'] },
    ],
  },

  'Ratings': {
    stack: 'Cowork task · headless Chrome scrape · Supabase JSON · Next.js API',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['nutriobox-ratings-weekly-refresh, cron 0 8 * * 1 (Mon)'],
        edge: '' },
      { stage: 'SCRAPE — browser (per outlet ×10)',
        detail: ['Google knowledge-panel aria-label', 'Zomato JSON-LD aggregateRating; Swiggy dineout/delivery', 'baseline = current ratings.json (keep prior on null)'],
        edge: '' },
      { stage: 'UPLOAD — Supabase (curl x-upsert)',
        detail: ['reports/ratings.json (current) + reports/ratings-history.json (ISO week)'],
        edge: '' },
      { stage: 'SERVE — Next.js',
        detail: ['/api/ratings (≈60s edge cache) → /dashboard/ratings', 'data-only: no git deploy needed'] },
    ],
  },

  'Music Monitor': {
    stack: 'Next.js route (live view)',
    nodes: [
      { stage: 'LIVE PAGE — Next.js',
        detail: ['/dashboard/music', 'No scheduled job — reflects live device state for 9 outlets'] },
    ],
  },

  'Vehicle Monitoring Dashboard': {
    stack: 'Windows Task Scheduler ~20:00 IST · Python + requests · OneLap (Traccar) API · Nominatim/OSM · openpyxl · git→Vercel · Gmail SMTP',
    nodes: [
      { stage: 'TRIGGER — Windows Task Scheduler',
        detail: ['automation\\vehicle_report\\RUN-vehicle-report.bat → python vehicle_report.py [YYYY-MM-DD?]', 'Setup schedules ~8:00 PM IST (the sketch says 7 PM); back-date on demand: RUN-vehicle-report.bat 2026-08-11', 'Secrets in vehicle_report_config.py (git-ignored): OneLap email/password + Gmail App Password'],
        edge: 'per vehicle ↓' },
      { stage: 'LOGIN — OneLap = Traccar API (NOT Playwright)',
        detail: ['Plain HTTPS via python-requests — no browser', 'POST https://web.onelap.in/api/session  (data: email, password)', 'GET /api/devices → the vehicle list'],
        edge: '' },
      { stage: 'PULL TRIPS PER VEHICLE',
        detail: ['GET /api/reports/summary?deviceId=&from=&to= → distance; skip if < 5 km (MIN_KM)', 'GET /api/reports/trips?deviceId=&from=&to= → start/end time, start/end lat-lon, distance, duration', 'window = local midnight → now (UTC ISO); back-dated run uses 23:59'],
        edge: '' },
      { stage: 'DETECT STOPS + MAP TO OUTLETS',
        detail: ['gap between trips ≥ 15 min (STOP_MIN) = a delivery stop', 'nearest_outlet() via haversine; ≤ 1800 m (NEAR_OUTLET) ⇒ that outlet’s name, else geocode', 'Depot (28.6221, 77.3787) “NutrioBox (Noida 63) – Depot”; “returned” if last point < 1300 m of depot'],
        branches: ['OUTLETS dict = 9 outlets (lat/long)', 'checkpoints sampled at 30 / 60 / 90 / 120 min'],
        edge: '' },
      { stage: 'GEOCODE — Nominatim / OpenStreetMap (NOT Google)',
        detail: ['GET nominatim.openstreetmap.org/reverse?lat=&lon=&zoom=16', 'label = road, suburb, town; result cached + 1.1s rate-limit', 'User-Agent NutrioBox-VehicleReport/1.0'],
        edge: '' },
      { stage: 'BUILD OUTPUTS — openpyxl + JSON',
        detail: ['Excel: load vehicle_movement_template.xlsx → one sheet per vehicle → reports\\Vehicle_Movement_Report_<date>.xlsx', 'Dashboard data: merge the day into public/vehicle-monitoring-data.json { date: {depot, window, V, LEGS} }'],
        edge: '' },
      { stage: 'PUBLISH — git → Vercel (NOT Supabase)',
        detail: ['git add public/vehicle-monitoring-data.json + public/vehicle-monitoring-dashboard.html', 'commit as user.email=mayank@nutriobox.com (Vercel-verified) → push origin main → Vercel', 'was ops@nutriobox.com until 18 Aug — that unverified email got the 12 Aug deploy BLOCKED; now fixed'],
        edge: '' },
      { stage: 'EMAIL — Gmail SMTP',
        detail: ['smtplib SMTP_SSL smtp.gmail.com:465 with a Gmail App Password (not a browser login)', 'sends the .xlsx attachment to satvik@nutriobox.com'],
        edge: '' },
      { stage: 'SERVE — Next.js on Vercel',
        detail: ['/dashboard/vehicle-monitoring reads public/vehicle-monitoring-data.json (date filter over history)'] },
    ],
  },

  'Daily Dashboard': {
    stack: 'Cowork task · Petpooja DOM · Google Sheets · DashboardNav gid map',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['petpooja-sales-to-gsheet, cron 30 10 * * * (10:30 IST)', 'targets the Windows Chrome deviceId (not macOS)'],
        edge: '' },
      { stage: 'READ — Petpooja dashboard (DOM)',
        detail: ['billing.petpooja.com/users/dashboard; jQuery daterangepicker → yesterday, List view', 'per-outlet <tr>/<td>; online-sales kebab tooltip → Zomato/Swiggy'],
        edge: '' },
      { stage: 'WRITE — Google Sheet',
        detail: ['Sheet 1r9u4DMs…vqs, weekday tab (DAY_GIDS)', 'B–K=10 outlets; L=SUM, N=round(NetSales), O=N/L, S=(L*0.95)/R, U=100−T'],
        edge: '' },
      { stage: 'SERVE — DashboardNav',
        detail: ['buildDailyUrl(): gid by IST weekday → opens Google Sheet'] },
    ],
  },

  'Weekly Dashboard': {
    stack: 'Cowork tasks (×3) · Petpooja/Zomato/Swiggy reports · openpyxl · Apps Script · DashboardNav',
    nodes: [
      { stage: 'TRIGGERS — Cowork tasks',
        detail: ['weekly-petpooja-sales-report: cron 0 3 * * 3 (Wed 3 AM)', 'petpooja-weekly-sales-sync: 30 12 * * 1', 'weekly-petpooja-dining-delivery-update: 0 8 * * 1'],
        edge: '' },
      { stage: 'SOURCES → SHEET COLUMNS',
        detail: ['PetPooja Sub-Order Wise → D–S', 'PetPooja KOT delivery-time → T–W', 'Zomato funnel → X–AH; Swiggy business-metrics xlsx (openpyxl) → AI–AR', 'Weekly KOT sheet → AS–AU'],
        edge: '' },
      { stage: 'WRITE — Apps Script',
        detail: ['Sheet 1oNCCGX…G0qpc, week tab, rows 5–23', 'single run() with self-verifying read-back (throws on blank)', 'Sale = My Amount − Discount + Container Charge'],
        edge: '' },
      { stage: 'SERVE — DashboardNav',
        detail: ['WEEKLY_GIDS map → opens last week tab'] },
    ],
  },

  'Daily KOT Comparison': {
    stack: 'Cowork task · Petpooja HTTP · Google Sheets · Supabase pointer JSON · DashboardNav runtime fetch',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['daily-kot-comparison, cron 0 5 * * * (5:10 IST); ≤80 tool calls'],
        edge: '' },
      { stage: 'READ — Petpooja',
        detail: ['KOT: items/kot_list, order_type[2,3] → "Showing 1..of N records"', 'Captain: custom_reports/view_report/27 → Total "No of Kots"', '9 outlets (config.KOT_OUTLETS)'],
        edge: '' },
      { stage: 'WRITE — Google Sheets',
        detail: ['SOURCE 1yOYpZBj…mn8: new "Dth Mmmm" tab, B2:B10 / C2:C10', 'DEST Sales Data 1r9u4DMs… "Daily KOT Comparsion" tab (mirror block)'],
        edge: '' },
      { stage: 'POINTER — Supabase',
        detail: ['PUT reports/kot-latest.json {sheetId,gid,tabName,date}', 'newest tab = leftmost (index 0)'],
        edge: '' },
      { stage: 'SERVE — DashboardNav',
        detail: ['useKotHref() fetches kot-latest.json at runtime → opens that gid', 'falls back to bare sheet URL on fetch failure'] },
    ],
  },

  'Weekly KOT Comparison': {
    stack: 'Cowork task · Petpooja HTTP · Google Sheets · Supabase pointer JSON · DashboardNav',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['kot-comparsion, cron 0 11 * * 1 (Mon ~11:06)'],
        edge: '' },
      { stage: 'READ — Petpooja (9 outlets)',
        detail: ['KOT items/kot_list order_type[2,3]; Captain view_report/27', 'window [Mon 13:00 → Mon 13:00)'],
        edge: '' },
      { stage: 'WRITE — Google Sheet',
        detail: ['Sheet 1eFBNV1b…QX30: duplicate newest tab → rename week → B/C', 'no native XHR/fetch patching; in-page jQuery submit'],
        edge: '' },
      { stage: 'POINTER + SERVE',
        detail: ['PUT reports/kot-weekly-latest.json', 'useWeeklyKotHref() resolves gid at runtime'] },
    ],
  },

  'Monthly KOT Comparison': {
    stack: 'Cowork task · Petpooja HTTP · Google Sheets · DashboardNav',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['monthly-kot-comparison, cron 0 11 1 * * (1st, 11:00)'],
        edge: '' },
      { stage: 'READ — Petpooja (9 outlets)',
        detail: ['KOT items/kot_list order_type[2,3]; Captain view_report/27', 'window [1st→1st) of the ended month'],
        edge: '' },
      { stage: 'WRITE — Google Sheet',
        detail: ['Sheet 1TFCNxjX…Nofw: "<Month Year>" tab, B/C (idempotent)'],
        edge: '' },
      { stage: 'SERVE — DashboardNav',
        detail: ['useMonthlyKotHref() → latest month tab'] },
    ],
  },

  'Momos Weekly Performance': {
    stack: 'Cowork task · Petpooja CSV · Higgsfield app (git) · self-hosted static HTML',
    nodes: [
      { stage: 'TRIGGER — Cowork task',
        detail: ['nutriobox-momos-dashboard--weekly-update-higgsfield, cron 45 5 * * 1'],
        edge: '' },
      { stage: 'SOURCE — Petpooja CSV',
        detail: ['Order Summary Item (10 outlets)', 'filter 6 Whole Wheat Momos SKUs; veg rule: startsWith("Chicken") ⇒ Nonveg', 'aggregate sales/units/orders/AOV per outlet + variant'],
        edge: '' },
      { stage: 'BUILD — Higgsfield app',
        detail: ['website_id a046de25-1608-…; edit app/src/routes/index.tsx const D', 'append 1 week to weekLabels/weekSpans/weekly + cumulative KPIs'],
        edge: '' },
      { stage: 'DEPLOY + SERVE',
        detail: ['website_repo_access clone → git push → deploy_website', 'ops card serves self-hosted /nutriobox-momos-dashboard.html (DEPLOY-momos.bat)'] },
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

/* ── Workflow modal — light-theme top-to-bottom flowchart ── */

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
  const tech = TECH[label];
  const [view, setView] = useState<'overview' | 'tech'>('overview');
  if (!flow) return null;
  const nodes = view === 'tech' && tech ? tech.nodes : flow.nodes;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${label} workflow`}
    >
      <div
        className="relative w-full max-w-lg max-h-[88vh] overflow-y-auto bg-white rounded-2xl shadow-2xl"
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
            </div>
            <div className="mt-1.5 flex items-center gap-1.5 text-[13px] font-medium text-brand-700">
              <ClockIcon />
              <span>{flow.schedule}</span>
            </div>
            {flow.tasks.length > 0 && (
              <div className="mt-1 text-[11px] text-slate-400 font-mono">{flow.tasks.join('  ·  ')}</div>
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

        {/* View toggle: manager overview vs developer architecture */}
        <div className="px-6 pt-4">
          <div className="inline-flex gap-0.5 p-0.5 bg-slate-100 rounded-lg">
            <button
              type="button"
              onClick={() => setView('overview')}
              className={`px-3 py-1 rounded-md text-[12.5px] font-medium transition-colors ${
                view === 'overview' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Overview
            </button>
            <button
              type="button"
              onClick={() => setView('tech')}
              disabled={!tech}
              className={`px-3 py-1 rounded-md text-[12.5px] font-medium transition-colors ${
                view === 'tech' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              } ${!tech ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              Technical
            </button>
          </div>
          {view === 'tech' && tech?.stack && (
            <div className="mt-2 text-[11.5px] text-slate-500">
              <span className="font-medium text-slate-600">Stack:</span> {tech.stack}
            </div>
          )}
        </div>

        {/* Flowchart */}
        <div className="px-6 pt-3 pb-6">
          <div className="flex flex-col items-stretch">
            {nodes.map((n, i) => {
              const branches = n.branches ?? [];
              const detail = n.detail ?? [];
              const isLast = i === nodes.length - 1;
              return (
                <div key={i} className="flex flex-col items-stretch">
                  {/* box */}
                  <div className="flex rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
                    <div className={`w-1.5 shrink-0 bg-gradient-to-b ${accent}`} aria-hidden="true" />
                    <div className="px-4 py-3 flex-1 min-w-0">
                      <div className="text-[13.5px] font-bold text-slate-900 tracking-wide">{n.stage}</div>
                      {detail.map((d, j) => (
                        <div key={j} className="mt-1 text-[13px] text-slate-600 leading-relaxed">{d}</div>
                      ))}
                      {branches.length > 0 && (
                        <div className="mt-2.5 pl-1 font-mono text-[12px] text-slate-500 space-y-1">
                          {branches.map((b, j) => (
                            <div key={j} className="whitespace-pre-wrap">
                              {(j === branches.length - 1 ? '└── ' : '├── ') + b}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* connector + arrow */}
                  {!isLast && (
                    <div className="flex flex-col items-center py-1.5">
                      {n.edge ? (
                        <div className="max-w-sm text-center text-[11.5px] italic text-slate-400 mb-0.5">{n.edge}</div>
                      ) : (
                        <span className="block w-px h-2 bg-slate-200" aria-hidden="true" />
                      )}
                      <span className="text-slate-300">
                        <DownArrow />
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
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
