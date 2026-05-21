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
      {/* ── Background: cream left / green right split ── */}
      <div className="absolute inset-0 flex">
        <div className="w-[42%] h-full" style={{ backgroundColor: '#f6f5f0' }} />
        <div className="flex-1 h-full" style={{ backgroundColor: '#357953' }} />
      </div>

      {/* ── Angled green overlay — the tilted rectangle from the original design ── */}
      <div
        className="absolute z-[1]"
        style={{
          top: '-10%',
          left: '30%',
          width: '45%',
          height: '120%',
          backgroundColor: '#357953',
          transform: 'rotate(8deg)',
          transformOrigin: 'top left',
          borderRadius: '0 0 40px 0',
        }}
      />

      {/* ── Small decorative green square (top-left accent) ── */}
      <div
        className="absolute z-[2]"
        style={{
          top: '8%',
          left: '38%',
          width: '28px',
          height: '28px',
          backgroundColor: '#2d6b47',
          borderRadius: '6px',
        }}
      />
      {/* ── Small decorative cream square on green side ── */}
      <div
        className="absolute z-[2]"
        style={{
          top: '42%',
          left: '56%',
          width: '20px',
          height: '20px',
          backgroundColor: '#f6f5f0',
          borderRadius: '4px',
          opacity: 0.3,
        }}
      />

      {/* ── Nutriobox logo — top left ── */}
      <div className="absolute top-[3%] left-[2.5%] z-10">
        <Image
          src="/nutriobox-logo.png"
          alt="Nutriobox"
          width={220}
          height={80}
          className="h-16 w-auto object-contain"
          priority
        />
      </div>

      {/* ── Tagline text — left side ── */}
      <div
        className="absolute z-10 flex flex-col justify-center px-[5%]"
        style={{
          top: '18%',
          left: '0%',
          width: '50%',
          height: '38%',
        }}
      >
        <div className="flex gap-3 mb-5">
          <span className="inline-block rounded-full bg-white/90 border border-slate-200 px-4 py-1.5 text-sm font-medium text-slate-700 shadow-sm">
            Sales analytics
          </span>
          <span className="inline-block rounded-full bg-[#c8f169] px-4 py-1.5 text-sm font-medium text-slate-800 shadow-sm">
            Delivery insights
          </span>
        </div>
        <h1
          className="font-bold text-[#1e3a2a] leading-[1.05] tracking-tight"
          style={{ fontSize: 'clamp(2rem, 4.5vw, 4.2rem)' }}
        >
          Your operations,<br />simplified.
        </h1>
        <div className="flex flex-wrap gap-3 mt-5 items-center">
          <span className="inline-block rounded-full bg-white/90 border border-slate-200 px-4 py-1.5 text-sm font-medium text-slate-700 shadow-sm">
            Menu planning
          </span>
          <span className="text-sm font-medium text-slate-500">
            more from a
          </span>
          <span className="inline-block rounded-full bg-[#c8f169] px-4 py-1.5 text-sm font-medium text-slate-800 shadow-sm">
            single dashboard
          </span>
        </div>
      </div>

      {/* ── White rounded card + login form — right side ── */}
      <div
        className="absolute z-10 flex items-start justify-center"
        style={{
          top: '8%',
          right: '3%',
          width: '35%',
          height: '58%',
        }}
      >
        <div
          className="w-full h-full rounded-[2rem] bg-white/95 shadow-xl backdrop-blur-sm flex items-start justify-center pt-10"
        >
          <div className="w-full max-w-sm px-8">
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

      {/* ── Food image at bottom ── */}
      <div
        className="absolute bottom-0 left-0 right-0 z-[5] h-[38%] bg-cover bg-bottom bg-no-repeat"
        style={{ backgroundImage: "url('/login-food.png')" }}
      />
      {/* Gradient blend at top of food image */}
      <div className="absolute bottom-[27%] left-0 right-0 z-[6] h-[12%]">
        <div
          className="h-full w-[42%] float-left"
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
    </div>
  );
}
