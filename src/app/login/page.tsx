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
      {/* ── Background: the exact original design image ── */}
      <div
        className="absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/Web-Banner-02.png')" }}
      />

      {/* ── Cover "Allsure Services Pvt. Ltd." with cream patch ── */}
      <div
        className="absolute top-0 left-0 z-10"
        style={{ width: '39%', height: '15%', backgroundColor: '#f6f5f0' }}
      />

      {/* ── Nutriobox logo in place of Allsure text ── */}
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

      {/* ── Cover "Sukhna Foods + Nutriobox" logos (cream portion) ── */}
      <div
        className="absolute z-10"
        style={{
          top: '48%',
          left: '0%',
          width: '44%',
          height: '30%',
          backgroundColor: '#f6f5f0',
        }}
      />
      {/* ── Cover "Sukhna Foods + Nutriobox" logos (green portion) ── */}
      <div
        className="absolute z-10"
        style={{
          top: '48%',
          left: '44%',
          width: '22%',
          height: '30%',
          backgroundColor: '#357953',
        }}
      />

      {/* ── Login form inside the white card area ── */}
      <div
        className="absolute z-30 flex items-start justify-center pt-10"
        style={{
          top: '10%',
          right: '3%',
          width: '35%',
          height: '58%',
        }}
      >
        <div className="w-full max-w-sm px-6">
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
