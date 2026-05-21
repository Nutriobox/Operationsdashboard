import Link from 'next/link';
import { supabaseServer } from '@/lib/supabase/server';
import LogoutButton from './LogoutButton';

export default async function Navbar() {
  const supabase = supabaseServer();
  const {
    data: { user }
  } = await supabase.auth.getUser();

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand to-brand-700 flex items-center justify-center shadow-sm">
            <span className="text-white font-bold text-sm">N</span>
          </div>
          <span className="font-semibold text-lg tracking-tight text-slate-900 group-hover:text-brand-700 transition-colors">
            Nutriobox
          </span>
        </Link>

        {/* Right side */}
        <div className="flex items-center gap-1 text-sm">
          <Link
            href="/"
            className="px-3 py-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-medium transition-colors"
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            className="px-3 py-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 font-medium transition-colors"
          >
            Dashboard
          </Link>

          {user ? (
            <>
              <div className="w-px h-5 bg-slate-200 mx-2" />
              <span className="text-slate-400 text-xs truncate max-w-[160px]">{user.email}</span>
              <LogoutButton />
            </>
          ) : (
            <>
              <div className="w-px h-5 bg-slate-200 mx-2" />
              <Link
                href="/login"
                className="px-4 py-2 rounded-lg bg-brand text-white font-medium hover:bg-brand-700 shadow-sm hover:shadow transition-all"
              >
                Log in
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
