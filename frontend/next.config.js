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
  // Set base path if deploying to a subdirectory
  // basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  // trailingSlash: true, // Optional: for GitHub Pages compatibility
};

module.exports = nextConfig;
