'use client';

import { usePathname } from 'next/navigation';
import DashboardNav from '@/components/DashboardNav';
import DashboardCards from '@/components/DashboardCards';
import { SalesPreloadProvider } from '@/components/SalesPreload';

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
  const isHome = pathname === '/dashboard';
  const isFullPageReport =
    pathname === '/dashboard/sales-item' ||
    pathname === '/dashboard/discount-codes' ||
    pathname === '/dashboard/delay';

  /* ── Landing page: welcome header + dashboard cards ── */
  /* SalesPreloadProvider starts loading the 116MB sales report in a hidden  */
  /* iframe so it's ready by the time the user clicks through.              */
  if (isHome) {
    return (
      <SalesPreloadProvider>
        <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-slate-50 to-white">
          {/* Hero section */}
          <div className="mx-auto max-w-7xl px-6 pt-12 pb-4">
            <div className="animate-fade-in">
              <p className="text-sm font-medium text-brand-600 tracking-wide uppercase">
                Operations Hub
              </p>
              <h1 className="mt-2 text-3xl md:text-4xl font-bold text-slate-900 tracking-tight">
                Welcome back, {name}
              </h1>
              <p className="mt-2 text-slate-500 text-base max-w-xl">
                Access your dashboards and reports from one place. Select a dashboard below to get started.
              </p>
            </div>
          </div>

          {/* Dashboard cards grid */}
          <div className="mx-auto max-w-7xl px-6 pt-4 pb-16 animate-slide-up">
            <DashboardCards />
          </div>
        </div>
      </SalesPreloadProvider>
    );
  }

  /* ── Full-page reports: no chrome ── */
  if (isFullPageReport) {
    return <>{children}</>;
  }

  /* ── Other sub-routes: header + pill nav + children ── */
  return (
    <div className="min-h-[calc(100vh-4rem)]">
      <header className="mx-auto max-w-7xl px-6 pt-10 pb-2 text-slate-900">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Welcome back, {name}</h1>
        <p className="mt-1 text-slate-500 text-sm">
          Your <span className="capitalize font-medium text-slate-700">{segment}</span> plan dashboard
        </p>
      </header>

      <div className="mt-4 mb-6">
        <DashboardNav />
      </div>

      <div>{children}</div>
    </div>
  );
}
