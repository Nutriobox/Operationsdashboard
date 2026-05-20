import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Office IPs - apna office ka public IP yahan daalo
const ALLOWED_IPS = [
  '122.176.138.21',  // Noida office IP
  // Add more IPs if needed
];

// IP restriction sirf non-logged-in users ke liye.
// Trusted devices bypass the IP check via a long-lived cookie set by
// /api/enroll/<secret>. Useful for the 4-5 laptops/phones that need
// access from anywhere (home wifi, mobile data, etc.) without exposing
// the login page to the whole internet.
const IP_RESTRICTED = process.env.ENABLE_IP_RESTRICTION === 'true';
const TRUSTED_DEVICE_SECRET = process.env.TRUSTED_DEVICE_SECRET || '';
const TRUSTED_COOKIE = 'nb_trusted_device';

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Check IP restriction for login/signup pages
  if (IP_RESTRICTED) {
    const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
    const isAllowedIP = ALLOWED_IPS.some(allowed => ip.startsWith(allowed));

    // Trusted device cookie bypasses the IP allowlist.
    const trustedCookie = request.cookies.get(TRUSTED_COOKIE)?.value;
    const isTrustedDevice =
      TRUSTED_DEVICE_SECRET.length > 0 && trustedCookie === TRUSTED_DEVICE_SECRET;

    const isLoginPage =
      request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup';

    // Block login/signup from unknown IPs unless the device is trusted.
    if (isLoginPage && !isAllowedIP && !isTrustedDevice) {
      return new NextResponse('Access Denied', { status: 403 });
    }
  }

  // Supabase auth check for dashboard
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => request.cookies.getAll().map(c => ({ name: c.name, value: c.value })),
        setAll: (cookies: { name: string; value: string; options: CookieOptions }[]) =>
          cookies.forEach(({ name, value, options }) => response.cookies.set(name, value, options)),
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();

  if (!user && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return response;
}

export const config = {
  matcher: ['/dashboard/:path*', '/login', '/signup'],
};
