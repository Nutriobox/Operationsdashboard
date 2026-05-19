// Sales Item Dashboard - embeds the latest report from Supabase Storage.
// The file is too large for git so it lives in the public "reports" bucket
// and is refreshed daily by scripts/upload-dashboard.ps1.
const REPORT_URL =
  'https://jkzremlkrxhhshqouudk.supabase.co/storage/v1/object/public/reports/sales-dashboard.html';

export default function SalesItemDashboardPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-10">
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <iframe
          src={REPORT_URL}
          title="Sales Item Dashboard"
          className="block w-full border-0 bg-white"
          style={{ height: 'calc(100vh - 220px)', minHeight: '720px' }}
        />
      </div>
    </div>
  );
}
