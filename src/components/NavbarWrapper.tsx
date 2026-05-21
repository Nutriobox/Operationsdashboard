'use client';

import { usePathname } from 'next/navigation';
import { type ReactNode } from 'react';

// Hides children (Navbar) on specific routes like /login
export default function NavbarWrapper({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (pathname === '/login') return null;
  return <>{children}</>;
}
