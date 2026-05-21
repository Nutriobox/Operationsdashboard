'use client';

import { useState, useCallback } from 'react';

// Sales Item Dashboard - full-page report viewer with loading indicator.
// The Power BI report is ~116MB uncompressed (~9.5MB gzipped) and takes
// 10-15s to load. We show a professional loading overlay while it loads.

export default function SalesItemDashboardPage() {
  const [loading, setLoading] = useState(true);

  const handleLoad = useCallback(() => {
    setLoading(false);
  }, []);

  return (
    <div className="relative" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Loading overlay */}
      {loading && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white">
          {/* Animated spinner */}
          <div className="relative">
            <div className="w-12 h-12 rounded-full border-[3px] border-slate-200" />
            <div className="absolute inset-0 w-12 h-12 rounded-full border-[3px] border-transparent border-t-emerald-500 animate-spin" />
          </div>

          <p className="mt-5 text-sm font-medium text-slate-700">
            Loading Sales Dashboard
          </p>
          <p className="mt-1.5 text-xs text-slate-400 max-w-xs text-center">
            This report is data-heavy and may take a few seconds to fully render.
          </p>

          {/* Subtle progress bar animation */}
          <div className="mt-6 w-48 h-1 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full"
              style={{
                animation: 'loadProgress 12s ease-out forwards',
              }}
            />
          </div>

          <style>{`
            @keyframes loadProgress {
              0%   { width: 0%; }
              20%  { width: 30%; }
              50%  { width: 60%; }
              80%  { width: 85%; }
              100% { width: 95%; }
            }
          `}</style>
        </div>
      )}

      {/* Iframe - always mounted so it starts loading immediately */}
      <iframe
        src="/api/sales-dashboard"
        title="Sales Item Dashboard"
        className="block w-full h-full border-0 bg-white"
        onLoad={handleLoad}
      />
    </div>
  );
}
