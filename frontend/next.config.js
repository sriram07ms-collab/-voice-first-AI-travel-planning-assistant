/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Enable static export for GitHub Pages
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
  },
  // Set base path for GitHub Pages subdirectory deployment
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '/-voice-first-AI-travel-planning-assistant',
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || '/-voice-first-AI-travel-planning-assistant',
  trailingSlash: true, // Required for GitHub Pages compatibility
};

module.exports = nextConfig;
