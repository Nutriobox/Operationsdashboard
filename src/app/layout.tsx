import './globals.css';
import type { Metadata } from 'next';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Nutriobox',
  description: 'Personalized dashboards and category insights for your business.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
