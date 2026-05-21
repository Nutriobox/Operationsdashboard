// Sales Item Dashboard — this page renders nothing.
// The actual iframe is managed by SalesPreloadProvider in DashboardChrome,
// which keeps a single persistent iframe alive across route changes.
// When the pathname is /dashboard/sales-item, the provider flips the
// pre-loaded iframe from off-screen to visible — instant, no re-parse.

export default function SalesItemDashboardPage() {
  return null;
}
