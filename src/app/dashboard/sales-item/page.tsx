// Sales Item Dashboard - full-page report viewer.
// Fills the viewport below the top navbar (3.5rem high), no surrounding chrome.
// We proxy through /api/sales-dashboard so the report is served with the right
// content-type and without Supabase's sandbox CSP (which would block JS).
export default function SalesItemDashboardPage() {
  return (
    <iframe
      src="/api/sales-dashboard"
      title="Sales Item Dashboard"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
