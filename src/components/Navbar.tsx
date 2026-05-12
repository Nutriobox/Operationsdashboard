import Link from 'next/link';
import { supabaseServer } from '@/lib/supabase/server';
import LogoutButton from './LogoutButton';

export default async function Navbar() {
  const supabase = supabaseServer();
  const {
    data: { user }
  } = await supabase.auth.getUser();

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-lg text-brand-dark">
          Nutriobox
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/" className="hover:text-brand">Home</Link>
          <Link href="/dashboard" className="hover:text-brand">Dashboard</Link>
          {user ? (
            <>
              <span className="text-slate-500">{user.email}</span>
              <LogoutButton />
            </>
          ) : (
            <>
              <Link href="/login" className="hover:text-brand">Log in</Link>
              <Link
                href="/signup"
                className="px-3 py-1.5 rounded bg-brand text-white hover:bg-brand-dark"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
