// Discount Analytics — self-contained static report served from
// /public/nutriobox-discount-dashboard.html and shown in an iframe (same
// pattern as the Momos and Vehicle Monitoring dashboards). Rendering it as
// an in-app route keeps the Nutriobox navbar on top and browser Back working.
export default function DiscountAnalyticsPage() {
  return (
    <iframe
      src="/nutriobox-discount-dashboard.html"
      title="Discount Analytics"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
