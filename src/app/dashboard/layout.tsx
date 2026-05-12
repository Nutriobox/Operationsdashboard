import { redirect } from 'next/navigation';
import { supabaseServer } from '@/lib/supabase/server';
import DashboardChrome from '@/components/DashboardChrome';
import { firstName } from '@/lib/firstName';
import type { UserProfile } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = supabaseServer();
  const {
    data: { user }
  } = await supabase.auth.getUser();

  if (!user) redirect('/login');

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .maybeSingle();

  const p = profile as UserProfile | null;
  const name = firstName(
    p?.full_name ??
      (user.user_metadata?.full_name as string | undefined) ??
      user.email
  );
  const segment = p?.segment ?? 'starter';

  return (
    <DashboardChrome name={name} segment={segment}>
      {children}
    </DashboardChrome>
  );
}
