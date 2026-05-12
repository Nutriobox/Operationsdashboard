// GET    /api/categories          → list all
// POST   /api/categories          → create a new category (auth required)
import { NextRequest, NextResponse } from 'next/server';
import { supabaseServer } from '@/lib/supabase/server';

export async function GET() {
  const supabase = supabaseServer();
  const { data, error } = await supabase
    .from('categories')
    .select('*')
    .order('created_at', { ascending: false });
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ categories: data });
}

export async function POST(req: NextRequest) {
  const supabase = supabaseServer();
  const {
    data: { user }
  } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: 'unauthorized' }, { status: 401 });

  const body = await req.json();
  const { slug, title, description, hero_image_url } = body ?? {};

  if (!slug || !title) {
    return NextResponse.json({ error: 'slug and title are required' }, { status: 400 });
  }

  const { data, error } = await supabase
    .from('categories')
    .insert({ slug, title, description, hero_image_url })
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ category: data }, { status: 201 });
}
