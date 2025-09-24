/** @type {import('next').NextConfig} */
const nextConfig = {
  // External packages that should be treated as external in server components
  serverExternalPackages: ['@distube/ytdl-core'],
  
  // Security headers
  async headers() {
    const isDev = process.env.NODE_ENV !== 'production';
    const connectSrc = isDev
      ? "connect-src 'self' ws: wss: http://localhost:5000 http://127.0.0.1:5000;"
      : "connect-src 'self'";

    const csp = [
      "default-src 'self'",
      connectSrc,
      "img-src 'self' https: data:",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
    ].join('; ');

    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Content-Security-Policy', value: csp },
        ],
      },
    ];
  },

  // Proxy Next.js /api/* to Flask server in development and simple deployments
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',
      },
    ];
  },
  
  // Optimize images
  images: {
    domains: ['i.ytimg.com', 'img.youtube.com'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Production optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  
  // Enable compression
  compress: true,
  
  // Output configuration for static export if needed
  output: 'standalone',
};

export default nextConfig;
