import './globals.css';
import type { Metadata } from 'next';
import Navbar from '@/components/Navbar';
import NavbarWrapper from '@/components/NavbarWrapper';

export const metadata: Metadata = {
  title: 'Nutriobox',
  description: 'Personalized dashboards and category insights for your business.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <NavbarWrapper>
          <Navbar />
        </NavbarWrapper>
        <main>{children}</main>
      </body>
    </html>
  );
}
