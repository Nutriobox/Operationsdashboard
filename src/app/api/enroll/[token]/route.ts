// Trusted-device enrollment endpoint.
//
// A device owner opens https://<site>/api/enroll/<TRUSTED_DEVICE_SECRET>
// ONCE from each of their 4-5 laptops/phones. That call sets a long-lived
// HttpOnly cookie on the device. The middleware sees that cookie on
// subsequent requests and lets the device bypass the office-IP allowlist,
// so the team can use the dashboard from any network.
//
// To rotate or revoke: change TRUSTED_DEVICE_SECRET in Railway env vars.
// All previously-enrolled devices will then need to re-enroll with the
// new URL.

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const TRUSTED_COOKIE = 'nb_trusted_device';
const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

export async function GET(
  request: NextRequest,
  { params }: { params: { token: string } }
) {
  const expected = process.env.TRUSTED_DEVICE_SECRET || '';

  if (!expected) {
    return new NextResponse(
      'Trusted-device enrollment is not configured. ' +
        'Set TRUSTED_DEVICE_SECRET in Railway env vars.',
      { status: 500 }
    );
  }

  if (params.token !== expected) {
    return new NextResponse('Invalid enrollment token.', { status: 403 });
  }

  // Token matches - set the cookie and send the user to the login page.
  const response = NextResponse.redirect(new URL('/login', request.url));
  response.cookies.set({
    name: TRUSTED_COOKIE,
    value: expected,
    maxAge: ONE_YEAR_SECONDS,
    httpOnly: true,
    sameSite: 'lax',
    secure: true,
    path: '/',
  });
  return response;
}
