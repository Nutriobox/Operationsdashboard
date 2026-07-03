// Customer Feedback Dashboard - full-page customer feedback report.
// Mirrors the Delay Dashboard: fills the viewport below the top navbar,
// no welcome header or tab strip. The report HTML is hosted on Supabase
// Storage at reports/feedback-dashboard.html and re-served via the
// /api/feedback-dashboard route so its inline scripts and styles render
// correctly (Supabase's default storage MIME and sandbox CSP would otherwise
// break in-browser rendering).
export default function FeedbackDashboardPage() {
  return (
    <iframe
      src="/api/feedback-dashboard"
      title="Customer Feedback"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
