import Link from 'next/link';
import { supabaseServer } from '@/lib/supabase/server';
import type { Category } from '@/lib/types';

export const revalidate = 60; // ISR — page regenerates every 60s

export default async function HomePage() {
  const supabase = supabaseServer();
  const { data: categories } = await supabase
    .from('categories')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(6);

  const list = (categories ?? []) as Category[];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-12">
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold tracking-tight text-slate-900">
          Personalized insights for every customer
        </h1>
        <p className="mt-4 max-w-2xl mx-auto text-lg text-slate-600">
          Nutriobox delivers tailored dashboards and reports — segmented by category, customized per user.
        </p>
        <div className="mt-8 flex gap-3 justify-center">
          <Link href="/signup" className="px-6 py-3 rounded-md bg-brand text-white font-medium hover:bg-brand-dark">
            Get started
          </Link>
          <Link href="/dashboard" className="px-6 py-3 rounded-md border border-slate-300 font-medium hover:bg-white">
            View demo dashboard
          </Link>
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-6">Explore categories</h2>
        {list.length === 0 ? (
          <p className="text-slate-500">
            No categories yet — once you seed the <code>categories</code> table in Supabase they'll appear here.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {list.map((c) => (
              <Link
                key={c.id}
                href={`/category/${c.slug}`}
                className="block rounded-lg border border-slate-200 bg-white p-5 hover:shadow transition"
              >
                <h3 className="font-semibold text-lg">{c.title}</h3>
                <p className="mt-1 text-sm text-slate-600 line-clamp-3">{c.description}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
