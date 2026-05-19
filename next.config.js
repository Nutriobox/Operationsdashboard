/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // 'standalone' output omits the public/ folder from the deploy artifact,
  // which made /nutriobox-bg.jpg 404 in production. Standard output serves
  // public/ correctly under `next start`.
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '**.supabase.co' }
    ]
  }
};

module.exports = nextConfig;
