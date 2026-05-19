import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Office IPs - apna office ka public IP yahan daalo
const ALLOWED_IPS = [
  '122.176.138.21',  // Noida office IP
  // Add more IPs if needed
];

// IP restriction sirf non-logged-in users ke liye
// Logged-in users (3 laptops) kahi se bhi access kar sakte hain
const IP_RESTRICTED = process.env.ENABLE_IP_RESTRICTION === 'true';

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Check IP restriction for login page
  if (IP_RESTRICTED) {
    const ip = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown';
    const isAllowedIP = ALLOWED_IPS.some(allowed => ip.startsWith(allowed));
    const isLoginPage = request.nextUrl.pathname === '/login' || request.nextUrl.pathname === '/signup';

    // Block access to login/signup from unknown IPs
    if (isLoginPage && !isAllowedIP) {
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
