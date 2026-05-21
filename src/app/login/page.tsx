'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { supabaseBrowser } from '@/lib/supabase/client';

export default function LoginPage() {
  const router = useRouter();
  const supabase = supabaseBrowser();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
      return;
    }
    router.push('/dashboard');
    router.refresh();
  }

  return (
    <div className="relative flex min-h-[calc(100vh-4rem)] overflow-hidden">
      {/* ── Left panel: cream background with branding ── */}
      <div className="relative hidden lg:flex lg:w-[55%] flex-col bg-[#f5f1eb] px-12 py-10 overflow-hidden">
        {/* Nutriobox logo top-left */}
        <div className="relative z-10">
          <Image
            src="/nutriobox-brand-logo.jpg"
            alt="Nutriobox"
            width={160}
            height={46}
            className="h-10 w-auto object-contain"
            priority
          />
        </div>

        {/* Hero text */}
        <div className="relative z-10 mt-auto mb-auto -translate-y-8">
          {/* Floating labels */}
          <div className="flex items-center gap-3 mb-4">
            <span className="inline-flex items-center rounded-full bg-white px-4 py-1.5 text-sm font-medium text-emerald-700 shadow-sm">
              Manage leaves
            </span>
          </div>

          <h2 className="text-5xl xl:text-6xl font-extrabold text-[#2d5a3d] leading-[1.1] tracking-tight">
            Your workplace,
            <br />
            simplified.
          </h2>

          <div className="flex items-center gap-3 mt-5">
            <span className="inline-flex items-center rounded-full bg-white px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm">
              payslips
            </span>
            <span className="inline-flex items-center rounded-full bg-[#d4f542] px-4 py-1.5 text-sm font-medium text-slate-800 shadow-sm">
              more from a single dashboard
            </span>
          </div>
        </div>

        {/* Food image — bottom-left, positioned to overflow naturally */}
        <div className="absolute bottom-0 left-0 right-0 h-[45%] pointer-events-none">
          <Image
            src="/NutrioBox_web banner (1).png"
            alt="Nutriobox meals"
            fill
            className="object-cover object-top"
            sizes="55vw"
            priority
          />
          {/* Fade overlay so food blends into cream background at top */}
          <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-[#f5f1eb] to-transparent" />
        </div>
      </div>

      {/* ── Right panel: green background with login card ── */}
      <div className="relative flex w-full lg:w-[45%] flex-col items-center justify-center bg-[#3d7c53] px-6 py-12">
        {/* Decorative rounded white card — login form */}
        <div className="w-full max-w-md rounded-3xl bg-white p-10 shadow-2xl">
          {/* Mobile-only logo */}
          <div className="mb-6 lg:hidden flex justify-center">
            <Image
              src="/nutriobox-brand-logo.jpg"
              alt="Nutriobox"
              width={140}
              height={40}
              className="h-9 w-auto object-contain"
              priority
            />
          </div>

          <h1 className="text-2xl font-bold text-slate-900">Log in</h1>
          <p className="text-sm text-slate-500 mt-1">
            Welcome back. Sign in to access your dashboard.
          </p>

          <form onSubmit={onSubmit} className="mt-7 space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2.5">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-[#3d7c53] text-white py-3 font-semibold text-sm hover:bg-[#346a47] disabled:opacity-60 transition-colors shadow-sm"
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        {/* Subtle branding at bottom */}
        <p className="mt-8 text-sm text-white/60">
          Powered by Nutriobox
        </p>
      </div>
    </div>
  );
}
