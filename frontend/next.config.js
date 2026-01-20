/** @type {import('next').NextConfig} */
const isProduction = process.env.NODE_ENV === 'production';
const isStaticExport = process.env.NEXT_PUBLIC_STATIC_EXPORT === 'true';
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Only enable static export for production builds with static export flag
  ...(isStaticExport && {
    output: 'export',
    images: {
      unoptimized: true, // Required for static export
    },
  }),
  // Only set basePath/assetPrefix if specified (for GitHub Pages deployment)
  ...(basePath && {
    basePath: basePath,
    assetPrefix: basePath,
    trailingSlash: true, // Required for GitHub Pages compatibility
  }),
};

module.exports = nextConfig;
