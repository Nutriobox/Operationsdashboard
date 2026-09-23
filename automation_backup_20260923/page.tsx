// Daily Dashboard - redirects to the appropriate weekday tab in the Sales Data
// Google Sheet. "Daily" means yesterday's data (today's numbers aren't
// finalized yet). Server-side redirect so the browser jumps to Google Sheets
// instantly with no visible intermediate page.
import { redirect } from 'next/navigation';

export const dynamic = 'force-dynamic';

const SHEET_ID = '1r9u4DMsRzdExu50yuRT5kn21tsHx-vqs';

// Sunday=0 ... Saturday=6 mapped to the gid of that tab in the sheet.
const DAY_GIDS: Record<number, string> = {
  0: '1531957147', // Sun
  1: '417033488',  // Mon
  2: '2078196306', // Tues
  3: '1189627705', // Wed
  4: '169886895',  // Thur
  5: '1816270025', // Fri
  6: '1918686710', // Sat
};

function buildYesterdayUrl(): string {
  // Compute "yesterday" in IST regardless of where the server is.
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const yesterdayIst = new Date(Date.now() + IST_OFFSET_MS - 24 * 60 * 60 * 1000);
  const dayIndex = yesterdayIst.getUTCDay();
  const gid = DAY_GIDS[dayIndex];
  return `https://docs.google.com/spreadsheets/d/${SHEET_ID}/edit?gid=${gid}#gid=${gid}`;
}

export default function DailyDashboardPage() {
  redirect(buildYesterdayUrl());
}
