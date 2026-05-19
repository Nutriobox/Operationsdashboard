// Sales Item Dashboard - embeds the latest report from Supabase Storage.
// We go through /api/sales-dashboard rather than fetching the Supabase URL
// directly, because Supabase serves storage objects with a sandbox CSP that
// blocks JavaScript inside the iframe (charts wouldn't render). The API
// route re-serves the bytes from our origin with proper text/html headers.
export default function SalesItemDashboardPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-10">
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <iframe
          src="/api/sales-dashboard"
          title="Sales Item Dashboard"
          className="block w-full border-0 bg-white"
          style={{ height: 'calc(100vh - 220px)', minHeight: '720px' }}
        />
      </div>
    </div>
  );
}
