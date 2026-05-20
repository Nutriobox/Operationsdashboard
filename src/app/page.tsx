// No public landing page. Logged-out visitors go to /login, logged-in
// visitors go to /dashboard. The site is an internal tool, so there's
// nothing to show people who aren't authenticated.
import { redirect } from 'next/navigation';
import { supabaseServer } from '@/lib/supabase/server';

export const dynamic = 'force-dynamic';

export default async function HomePage() {
  const supabase = supabaseServer();
  const { data: { user } } = await supabase.auth.getUser();
  redirect(user ? '/dashboard' : '/login');
}
