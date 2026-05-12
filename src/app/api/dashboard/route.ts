// GET /api/dashboard
// Returns metrics + timeseries for the logged-in user.
// Replace the demo data with real aggregations from your tables.
import { NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';

export async function GET() {
  const supabase = supabaseServer();
  const {
    data: { user }
  } = await supabase.auth.getUser();

  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .maybeSingle();

  const metrics = [
    { label: 'Active categories', value: profile?.preferred_categories?.length ?? 0, delta_pct: 12 },
    { label: 'Reports generated', value: 42, delta_pct: 8 },
    { label: 'Engagement score', value: 87, delta_pct: -3 }
  ];

  const timeseries = Array.from({ length: 14 }, (_, i) => ({
    date: `D${i + 1}`,
    value: Math.round(60 + Math.sin(i / 2) * 20 + Math.random() * 10)
  }));

  return NextResponse.json({ metrics, timeseries, profile });
}
