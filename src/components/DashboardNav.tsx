'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/dashboard/sales-item', label: 'Sales Item Dashboard' },
  { href: '/dashboard/discount-codes', label: 'Discount Codes' },
  { href: '/dashboard/daily', label: 'Daily Dashboard' },
  { href: '/dashboard/weekly', label: 'Weekly Dashboard' }
];

export default function DashboardNav() {
  const pathname = usePathname();

  return (
    <div className="flex justify-center">
      <div className="inline-flex flex-wrap gap-2 rounded-full bg-white border border-slate-200 p-1.5 shadow-sm">
        {TABS.map((t) => {
          const isActive = pathname === t.href || pathname.startsWith(t.href + '/');
          return (
            <Link
              key={t.href}
              href={t.href}
              className={`px-5 py-2 text-sm font-medium rounded-full transition ${
                isActive
                  ? 'bg-brand text-white shadow'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              {t.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
