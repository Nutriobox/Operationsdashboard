'use client';

// Preloads the sales dashboard report in a hidden off-screen iframe while the
// user is on the landing page. When they navigate to /dashboard/sales-item,
// the report is already parsed and rendered — it appears instantly.
//
// The iframe lives in the DOM but is positioned off-screen (not display:none,
// because display:none prevents the browser from actually loading/rendering).

import { createContext, useContext, useState, useCallback, useRef } from 'react';

type PreloadState = {
  /** true once the hidden iframe has fired its onLoad event */
  ready: boolean;
  /** ref to the hidden iframe element — the sales page can reparent it */
  iframeRef: React.RefObject<HTMLIFrameElement | null>;
};

const SalesPreloadCtx = createContext<PreloadState>({
  ready: false,
  iframeRef: { current: null },
});

export function useSalesPreload() {
  return useContext(SalesPreloadCtx);
}

export function SalesPreloadProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement | null>(null);

  const handleLoad = useCallback(() => {
    setReady(true);
  }, []);

  return (
    <SalesPreloadCtx.Provider value={{ ready, iframeRef }}>
      {children}
      {/* Hidden iframe — loads the report off-screen */}
      <iframe
        ref={iframeRef}
        src="/api/sales-dashboard"
        title="Sales Dashboard Preload"
        onLoad={handleLoad}
        aria-hidden="true"
        tabIndex={-1}
        style={{
          position: 'fixed',
          top: '-200vh',
          left: '-200vw',
          width: '100vw',
          height: '100vh',
          border: 'none',
          pointerEvents: 'none',
          opacity: 0,
        }}
      />
    </SalesPreloadCtx.Provider>
  );
}
