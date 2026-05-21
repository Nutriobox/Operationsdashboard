'use client';

import { useState, useCallback } from 'react';

// Sales Item Dashboard — full-page report viewer.
//
// The 116MB Power BI report is preloaded in a hidden iframe on the landing
// page (SalesPreloadProvider in DashboardChrome). By the time the user
// clicks here, the browser has already cached /api/sales-dashboard (4-hour
// cache), so this iframe loads from disk cache almost instantly.
//
// The spinner is kept as a fallback for direct navigations or cold caches.

export default function SalesItemDashboardPage() {
  const [loading, setLoading] = useState(true);

  const handleLoad = useCallback(() => {
    setLoading(false);
  }, []);

  return (
    <div className="relative" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Loading fallback — only visible if cache miss (first visit of day / direct URL) */}
      {loading && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white">
          <div className="relative">
            <div className="w-12 h-12 rounded-full border-[3px] border-slate-200" />
            <div className="absolute inset-0 w-12 h-12 rounded-full border-[3px] border-transparent border-t-emerald-500 animate-spin" />
          </div>
          <p className="mt-5 text-sm font-medium text-slate-700">
            Loading Sales Dashboard
          </p>
          <p className="mt-1.5 text-xs text-slate-400 max-w-xs text-center">
            This report is data-heavy and may take a few seconds on first load.
          </p>
        </div>
      )}

      <iframe
        src="/api/sales-dashboard"
        title="Sales Item Dashboard"
        className="block w-full h-full border-0 bg-white"
        onLoad={handleLoad}
      />
    </div>
  );
}
