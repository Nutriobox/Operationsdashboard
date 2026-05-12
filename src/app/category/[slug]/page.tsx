export const dynamic = 'force-dynamic';
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { supabaseServer } from '@/lib/supabase/server';
import type { Category, UserProfile } from '@/lib/types';

export const revalidate = 120; // regenerate every 2 minutes

export async function generateStaticParams() {
  const supabase = supabaseServer();
  const { data } = await supabase.from('categories').select('slug');
  return (data ?? []).map((c: { slug: string }) => ({ slug: c.slug }));
}

export default async function CategoryPage({ params }: { params: { slug: string } }) {
  const supabase = supabaseServer();

  const { data: category } = await supabase
    .from('categories')
    .select('*')
    .eq('slug', params.slug)
    .maybeSingle();

  if (!category) return notFound();

  // If user is logged in, personalize the section ordering / CTA.
  const {
    data: { user }
  } = await supabase.auth.getUser();

  let profile: UserProfile | null = null;
  if (user) {
    const { data } = await supabase.from('profiles').select('*').eq('id', user.id).maybeSingle();
    profile = data as UserProfile | null;
  }

  const isPreferred = profile?.preferred_categories?.includes(category.slug);
  const cat = category as Category;

  return (
    <article className="mx-auto max-w-6xl px-4 py-8 space-y-8">
      <header>
        <p className="text-sm text-brand font-medium">Category</p>
        <h1 className="text-4xl font-bold mt-1">{cat.title}</h1>
        <p className="mt-3 text-lg text-slate-600 max-w-3xl">{cat.description}</p>
      </header>

      {profile && (
        <div
          className={`rounded-lg p-4 text-sm ${
            isPreferred ? 'bg-brand-light text-brand-dark' : 'bg-slate-100 text-slate-700'
          }`}
        >
          {isPreferred
            ? `This is one of your preferred categories — recommendations are tuned for your ${profile.segment} plan.`
            : `Not following this yet? Add it to your preferred categories for tailored insights.`}
        </div>
      )}

      <section className="prose max-w-none">
        <h2 className="text-2xl font-semibold">Overview</h2>
        <p>
          This page is rendered dynamically for <code>{cat.slug}</code>. Plug in real content from your{' '}
          <code>category_content</code> table to expand this section.
        </p>
      </section>

      <Link href="/" className="inline-block text-brand font-medium hover:underline">
        ← Back to all categories
      </Link>
    </article>
  );
}
