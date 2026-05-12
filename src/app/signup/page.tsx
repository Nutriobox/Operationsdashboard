'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabaseBrowser } from '@/lib/supabase/client';

export default function SignupPage() {
  const router = useRouter();
  const supabase = supabaseBrowser();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName } }
    });

    setLoading(false);

    if (error) {
      setError(error.message);
      return;
    }

    // Insert a profile row keyed by the new auth user.
    if (data.user) {
      await supabase.from('profiles').insert({
        id: data.user.id,
        email,
        full_name: fullName,
        segment: 'starter',
        preferred_categories: []
      });
    }

    router.push('/dashboard');
    router.refresh();
  }

  return (
    <div className="mx-auto max-w-md mt-16 mb-10 bg-white rounded-lg border border-slate-200 p-8">
      <h1 className="text-2xl font-semibold">Create account</h1>
      <p className="text-sm text-slate-600 mt-1">Start with a free starter account.</p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-sm font-medium">Full name</label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-brand text-white py-2 font-medium hover:bg-brand-dark disabled:opacity-60"
        >
          {loading ? 'Creating account…' : 'Sign up'}
        </button>
      </form>

      <p className="mt-6 text-sm text-slate-600">
        Already have an account?{' '}
        <Link href="/login" className="text-brand font-medium hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
