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
    <div className="relative min-h-screen bg-[#3d7c53] overflow-hidden flex">

      {/* ── Left side: branding + text ── */}
      <div className="relative z-20 hidden lg:flex lg:w-[50%] flex-col justify-center px-14 xl:px-20">
        {/* Nutriobox logo — use the PNG which has transparency */}
        <div className="mb-10">
          <Image
            src="/nutriobox-logo.png"
            alt="Nutriobox"
            width={180}
            height={52}
            className="h-12 w-auto object-contain"
            priority
          />
        </div>

        {/* Floating label */}
        <div className="flex items-center gap-3 mb-5">
          <span className="inline-flex items-center rounded-full bg-white/90 backdrop-blur-sm px-4 py-1.5 text-sm font-medium text-emerald-700 shadow-sm">
            Sales analytics
          </span>
        </div>

        {/* Main headline */}
        <h1 className="text-5xl xl:text-6xl font-extrabold text-white leading-[1.1] tracking-tight">
          Your operations,
          <br />
          simplified.
        </h1>

        <div className="flex flex-wrap items-center gap-3 mt-6">
          <span className="inline-flex items-center rounded-full bg-white/90 backdrop-blur-sm px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm">
            delivery insights
          </span>
          <span className="inline-flex items-center rounded-full bg-[#d4f542] px-4 py-1.5 text-sm font-medium text-slate-800 shadow-sm">
            all reports in one dashboard
          </span>
        </div>

        <p className="mt-8 text-white/70 text-base max-w-md leading-relaxed">
          Track sales performance, monitor delivery delays, and access discount analytics — all from a single hub.
        </p>
      </div>

      {/* ── Right side: login card with food peeking around it ── */}
      <div className="relative flex w-full lg:w-[50%] items-center justify-center px-6 py-12">
        {/* Food image background — subtle, behind the card */}
        <div
          className="absolute inset-0 bg-cover bg-center opacity-25"
          style={{ backgroundImage: "url('/login-food.png')" }}
        />
        {/* Green overlay so card stays readable */}
        <div className="absolute inset-0 bg-[#3d7c53]/50" />

        {/* White/cream rounded login card */}
        <div className="relative z-10 w-full max-w-md rounded-3xl bg-[#f9f7f3] p-10 shadow-2xl">
          {/* Mobile logo — only visible on small screens */}
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

          <h2 className="text-2xl font-bold text-slate-900">Log in</h2>
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
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
                placeholder="you@nutriobox.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
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
      </div>

      {/* ── Decorative food image — bottom-left, below text ── */}
      <div
        className="hidden lg:block absolute bottom-0 left-0 w-[50%] h-[35%] pointer-events-none z-10 bg-contain bg-left-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/login-food.png')" }}
      />
      {/* Gradient to blend food into the green bg at top */}
      <div className="hidden lg:block absolute bottom-0 left-0 w-[50%] h-[40%] pointer-events-none z-[11]">
        <div className="h-16 bg-gradient-to-b from-[#3d7c53] to-transparent" />
      </div>
    </div>
  );
}
