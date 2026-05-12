// Sales Item Dashboard — centred on the page with side margins, not edge-to-edge.
export default function SalesItemDashboardPage() {
  return (
    <div className="mx-auto max-w-6xl px-4 pb-10">
      <div className="rounded-lg border border-slate-200 bg-white overflow-hidden shadow-sm">
        <iframe
          src="/sales-dashboard.html"
          title="Sales Item Dashboard"
          className="block w-full border-0 bg-white"
          style={{ height: 'calc(100vh - 220px)', minHeight: '720px' }}
        />
      </div>
    </div>
  );
}
