'use client';

import { usePathname } from 'next/navigation';
import DashboardNav from '@/components/DashboardNav';

export default function DashboardChrome({
  name,
  segment,
  children
}: {
  name: string;
  segment: string;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  // /dashboard is the launcher screen — full-page background image, just the buttons.
  // Sub-routes (/dashboard/sales-item, etc.) show the welcome header + buttons + report.
  const isHome = pathname === '/dashboard';

  // 3.5rem = h-14 navbar height.
  // backgroundSize: 'contain' shows the entire image without cropping; the
  // green fallback colour fills any letterboxed area on aspect-ratio mismatch.
  const homeStyle: React.CSSProperties = {
    minHeight: 'calc(100vh - 3.5rem)',
    backgroundImage: "url('/nutriobox-bg.jpg')",
    backgroundColor: '#7BAE3E',
    backgroundSize: 'contain',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat'
  };

  if (isHome) {
    return (
      <div style={homeStyle} className="flex items-start justify-center pt-6">
        <DashboardNav />
      </div>
    );
  }

  return (
    <div>
      <header className="mx-auto max-w-6xl px-4 pt-12 pb-4 text-slate-900">
        <h1 className="text-4xl md:text-5xl font-bold">Welcome back, {name}</h1>
        <p className="mt-2 text-slate-600">
          Your <span className="capitalize font-medium">{segment}</span> plan dashboard
        </p>
      </header>

      <div className="mt-4 mb-6">
        <DashboardNav />
      </div>

      <div>{children}</div>
    </div>
  );
}
