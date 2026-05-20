// Deprecated - trusted-device enrollment was used when we had IP restriction.
// Now removed; this endpoint always returns 404 so any old links break loudly
// instead of silently doing the wrong thing.
import { NextResponse } from 'next/server';

export async function GET() {
  return new NextResponse('Not Found', { status: 404 });
}
