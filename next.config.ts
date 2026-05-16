import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'export', // Добавлено для сборки в обычный HTML на GitHub Pages
  images: {
    unoptimized: true, // Добавлено, так как на GitHub Pages не работает стандартное сжатие картинок Next.js
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
    ],
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
