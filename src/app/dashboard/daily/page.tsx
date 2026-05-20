// Daily Dashboard - redirects to the appropriate weekday tab in the Sales Data
// Google Sheet. "Daily" means yesterday's data, since today's numbers usually
// aren't finalized yet. Day-of-week is computed in IST so we always match
// the operations team's local day.
import { redirect } from 'next/navigation';

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

// Never cache - the redirect target depends on today's date.
export const dynamic = 'force-dynamic';

export default function DailyDashboardPage() {
  // Compute "yesterday" in IST (UTC+5:30) regardless of where the server runs.
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const yesterdayIst = new Date(Date.now() + IST_OFFSET_MS - 24 * 60 * 60 * 1000);
  const dayIndex = yesterdayIst.getUTCDay();
  const gid = DAY_GIDS[dayIndex];

  redirect(
    `https://docs.google.com/spreadsheets/d/${SHEET_ID}/edit?gid=${gid}#gid=${gid}`
  );
}
