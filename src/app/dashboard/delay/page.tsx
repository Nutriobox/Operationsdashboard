// Delay Dashboard - full-page delivery delay report.
// Mirrors the Sales Item Dashboard: fills the viewport below the top navbar,
// no welcome header or tab strip. The report HTML is hosted on Supabase
// Storage at reports/delay-dashboard.html and re-served via the
// /api/delay-dashboard route so its inline scripts and styles render
// correctly (Supabase's default storage MIME and sandbox CSP would otherwise
// break in-browser rendering).
export default function DelayDashboardPage() {
  return (
    <iframe
      src="/api/delay-dashboard"
      title="Delay Dashboard"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
