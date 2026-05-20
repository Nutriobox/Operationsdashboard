// Weekly Dashboard - redirects to the Weekly Sales Report Google Sheet on
// the tab for "last week from today's date". The sheet is structured with
// one tab per week, newest week first. We compute the Monday of "last week"
// in IST and look up that tab's gid in the map below.
//
// When a new week's tab gets added to the sheet, append it to WEEKLY_GIDS
// with the Monday of that week as the "start" key. The script picks the
// most recent start date that is <= "last week's Monday".
'use client';

import { useEffect, useState } from 'react';

const SHEET_ID = '1oNCCGX5ntgPW_OYwjWB5LMFhLfPitxzVAMWj95G0qpc';

// Sorted newest-first. Each entry is the Monday of that week.
// To add a new week: just prepend a new entry with the Monday's YYYY-MM-DD
// and the gid copied from the sheet tab's URL.
const WEEKLY_GIDS: Array<{ startMonday: string; gid: string; label: string }> = [
  { startMonday: '2026-05-11', gid: '282654557', label: 'May 11 - May 17, 2026' },
];

function buildLastWeekUrl(): string {
  // Compute the Monday of "last week" in IST.
  const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000;
  const nowIst = new Date(Date.now() + IST_OFFSET_MS);
  const dayOfWeek = nowIst.getUTCDay(); // 0=Sun ... 6=Sat
  // Days back to this week's Monday (treat Monday as 0 days back).
  const daysToThisMonday = (dayOfWeek + 6) % 7;
  const thisMonday = new Date(nowIst);
  thisMonday.setUTCDate(thisMonday.getUTCDate() - daysToThisMonday);
  // Last week's Monday is 7 days before this week's Monday.
  const lastMonday = new Date(thisMonday);
  lastMonday.setUTCDate(lastMonday.getUTCDate() - 7);
  const lastMondayKey = lastMonday.toISOString().slice(0, 10);

  // Find the most recent entry whose startMonday is <= lastMondayKey.
  const sorted = [...WEEKLY_GIDS].sort((a, b) => b.startMonday.localeCompare(a.startMonday));
  const match =
    sorted.find((e) => e.startMonday <= lastMondayKey) || sorted[0];

  const gid = match.gid;
  return `https://docs.google.com/spreadsheets/d/${SHEET_ID}/edit?gid=${gid}#gid=${gid}`;
}

export default function WeeklyDashboardPage() {
  const [url] = useState(buildLastWeekUrl);

  useEffect(() => {
    window.location.replace(url);
  }, [url]);

  return (
    <div className="mx-auto max-w-md text-center py-16 text-slate-600">
      <p>Opening last week&apos;s sales report in Google Sheets…</p>
      <p className="mt-3 text-sm">
        If it doesn&apos;t open in a moment,&nbsp;
        <a className="text-brand underline" href={url}>
          click here
        </a>
        .
      </p>
    </div>
  );
}
