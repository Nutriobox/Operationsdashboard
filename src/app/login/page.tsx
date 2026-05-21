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
    <div className="relative min-h-screen overflow-hidden">
      {/* ── Background: the original design image ── */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/Web-Banner-02.png')" }}
      />

      {/* ── Patch: cover "Allsure Services Pvt. Ltd." with cream ── */}
      <div
        className="absolute top-0 left-0 z-10"
        style={{ width: '39%', height: '15.5%', backgroundColor: '#f6f5f0' }}
      />

      {/* ── Patch: cover HR headline text area (cream side) ── */}
      <div
        className="absolute z-10"
        style={{
          top: '15%',
          left: '0%',
          width: '46%',
          height: '42%',
          backgroundColor: '#f6f5f0',
        }}
      />
      {/* ── Patch: cover HR headline text area (green side) ── */}
      <div
        className="absolute z-10"
        style={{
          top: '15%',
          left: '46%',
          width: '17%',
          height: '42%',
          backgroundColor: '#357953',
        }}
      />

      {/* ── Replacement text overlay ── */}
      <div
        className="absolute z-20 flex flex-col justify-center px-[5%]"
        style={{
          top: '16%',
          left: '0%',
          width: '60%',
          height: '40%',
        }}
      >
        <div className="flex gap-3 mb-4">
          <span className="inline-block rounded-full bg-white/90 border border-slate-200 px-4 py-1.5 text-sm font-medium text-slate-700">
            Sales analytics
          </span>
          <span className="inline-block rounded-full bg-[#c8f169] px-4 py-1.5 text-sm font-medium text-slate-800">
            Delivery insights
          </span>
        </div>
        <h1
          className="font-bold text-slate-900 leading-[1.05] tracking-tight"
          style={{ fontSize: 'clamp(2rem, 4.5vw, 4.2rem)' }}
        >
          Your operations,<br />simplified.
        </h1>
        <div className="flex gap-3 mt-4">
          <span className="inline-block rounded-full bg-white/90 border border-slate-200 px-4 py-1.5 text-sm font-medium text-slate-700">
            Menu planning
          </span>
          <span className="text-sm font-medium text-slate-600 flex items-center">
            more from a
          </span>
          <span className="inline-block rounded-full bg-[#c8f169] px-4 py-1.5 text-sm font-medium text-slate-800">
            single dashboard
          </span>
        </div>
      </div>

      {/* ── Patch: cover "Sukhna Foods + Nutriobox" logos in center ── */}
      <div
        className="absolute z-10"
        style={{
          top: '57%',
          left: '13%',
          width: '32%',
          height: '14%',
          backgroundColor: '#f6f5f0',
        }}
      />
      {/* Green patch for the right portion of the logo bar */}
      <div
        className="absolute z-10"
        style={{
          top: '57%',
          left: '45%',
          width: '8%',
          height: '14%',
          backgroundColor: '#357953',
        }}
      />

      {/* ── Patch: cover old food items at bottom-left ── */}
      <div
        className="absolute bottom-0 left-0 z-10"
        style={{ width: '44%', height: '33%', backgroundColor: '#f6f5f0' }}
      />
      {/* Green patch for bottom-right of old food */}
      <div
        className="absolute bottom-0 z-10"
        style={{ left: '44%', width: '10%', height: '33%', backgroundColor: '#357953' }}
      />

      {/* ── Nutriobox logo — replaces Allsure text ── */}
      <div className="absolute top-[3%] left-[2.5%] z-20">
        <Image
          src="/nutriobox-logo.png"
          alt="Nutriobox"
          width={220}
          height={80}
          className="h-16 w-auto object-contain"
          priority
        />
      </div>

      {/* ── New food image (Photo 3) at bottom ── */}
      <div
        className="absolute bottom-0 left-0 right-0 z-20 h-[36%] bg-cover bg-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/login-food.png')" }}
      />
      {/* Gradient blend at top of food image */}
      <div className="absolute bottom-[25%] left-0 right-0 z-[21] h-[12%]">
        <div
          className="h-full w-[44%] float-left"
          style={{
            background: 'linear-gradient(to bottom, #f6f5f0, transparent)',
          }}
        />
        <div
          className="h-full"
          style={{
            background: 'linear-gradient(to bottom, #357953, transparent)',
          }}
        />
      </div>

      {/* ── Login form — positioned over the white card in the image ── */}
      <div
        className="absolute z-30 flex items-start justify-center pt-8"
        style={{
          top: '12%',
          right: '3%',
          width: '35%',
          height: '55%',
        }}
      >
        <div className="w-full max-w-sm px-6">
          {/* Mobile logo fallback */}
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
                className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
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
                className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50/80 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-shadow"
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
    </div>
  );
}
