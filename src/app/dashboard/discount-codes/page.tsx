// Discount Codes - full-page daily offer tracker report.
// Mirrors the Sales Item Dashboard: fills the viewport below the top navbar,
// no welcome header or tab strip. The report HTML is pulled from the daily
// "NutrioBox Daily Offer Tracker" email and hosted on Supabase Storage;
// /api/discount-codes-report re-serves it with the right content-type so
// any inline styles inside the email render properly.
export default function DiscountCodesPage() {
  return (
    <iframe
      src="/api/discount-codes-report"
      title="Discount Codes"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
