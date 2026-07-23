// Music Monitor — Ookaradio background-music dashboard for all 9 outlets.
// Mirrors the Delay Dashboard: fills the viewport below the top navbar, no
// welcome header or tab strip. The dashboard is a self-contained static file
// served from /public (music-dashboard.html). It reads the Ookaradio Supabase
// project directly (data is anon-readable), and its own sign-in screen is
// stripped out because this page already sits behind the Operations Dashboard
// login.
export default function MusicMonitorPage() {
  return (
    <iframe
      src="/music-dashboard.html"
      title="Music Monitor"
      className="block w-full border-0 bg-white"
      style={{ height: 'calc(100vh - 3.5rem)' }}
    />
  );
}
