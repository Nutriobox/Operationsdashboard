// Momos Weekly Performance — self-contained static report served from
// /public/nutriobox-momos-dashboard.html and shown in an iframe (same
// pattern as the Vehicle Monitoring Dashboard). Rendering it as an in-app
// route (instead of linking straight to the raw .html) keeps the Nutriobox
// navbar on top — logo returns to the home screen and browser Back works.
export default function MomosDashboardPage() {
  return (
    <iframe
      src="/nutriobox-momos-dashboard.html"
      title="Momos Weekly Performance"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
