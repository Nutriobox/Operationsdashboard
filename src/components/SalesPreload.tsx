'use client';

// Persistent preload for the sales dashboard.
//
// Problem: the Power BI report is 116MB of HTML. Even with a warm HTTP cache,
// the browser needs ~8-10s just to parse and render that in a fresh iframe.
//
// Solution: keep ONE iframe alive across route changes. It starts loading on
// the landing page (hidden off-screen). When the user navigates to
// /dashboard/sales-item, we flip it to visible — instant, zero re-parse.
//
// This component wraps the entire dashboard layout. The sales-item page
// renders nothing of its own; it just tells this provider "show the iframe".

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
} from 'react';
import { usePathname } from 'next/navigation';

type PreloadState = {
  iframeReady: boolean;
};

const SalesPreloadCtx = createContext<PreloadState>({ iframeReady: false });

export function useSalesPreload() {
  return useContext(SalesPreloadCtx);
}

export function SalesPreloadProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [iframeReady, setIframeReady] = useState(false);

  const handleLoad = useCallback(() => {
    setIframeReady(true);
  }, []);

  // Should we show the iframe full-screen?
  const showFullScreen = pathname === '/dashboard/sales-item';
  // Should we preload? On the landing page OR if already on the sales page.
  const shouldMount = pathname === '/dashboard' || pathname === '/dashboard/sales-item';

  return (
    <SalesPreloadCtx.Provider value={{ iframeReady }}>
      {/* Page content — hidden when the sales iframe is shown full-screen */}
      <div style={{ display: showFullScreen ? 'none' : undefined }}>
        {children}
      </div>

      {/* The ONE persistent iframe. Positioned off-screen while preloading,
          moved into the viewport when the user is on /dashboard/sales-item. */}
      {shouldMount && (
        <div
          style={
            showFullScreen
              ? { height: 'calc(100vh - 4rem)' }
              : {
                  position: 'fixed',
                  top: '-200vh',
                  left: '-200vw',
                  width: '100vw',
                  height: '100vh',
                  pointerEvents: 'none',
                  opacity: 0,
                }
          }
        >
          {/* Show spinner overlay while iframe is loading on the sales page */}
          {showFullScreen && !iframeReady && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-white">
              <div className="relative">
                <div className="w-12 h-12 rounded-full border-[3px] border-slate-200" />
                <div className="absolute inset-0 w-12 h-12 rounded-full border-[3px] border-transparent border-t-emerald-500 animate-spin" />
              </div>
              <p className="mt-5 text-sm font-medium text-slate-700">
                Loading Sales Dashboard
              </p>
              <p className="mt-1.5 text-xs text-slate-400 max-w-xs text-center">
                Almost there — the report is rendering.
              </p>
            </div>
          )}

          {/* ?v=… is a cache-buster: each calendar hour gets a new URL, so the
              browser refetches at most once per hour even if it has a stale
              entry from an older deploy. The route now sends max-age=60 anyway,
              so within-the-hour edits still propagate within ~1 min. */}
          <iframe
            src={`/api/sales-dashboard?v=${Math.floor(Date.now() / 3_600_000)}`}
            title="Sales Item Dashboard"
            className="block w-full h-full border-0 bg-white"
            onLoad={handleLoad}
          />
        </div>
      )}
    </SalesPreloadCtx.Provider>
  );
}
