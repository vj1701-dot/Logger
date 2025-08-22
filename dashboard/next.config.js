/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  
  // API rewrites for development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.API_BASE_URL 
          ? `${process.env.API_BASE_URL}/api/:path*` 
          : 'http://localhost:8080/api/:path*'
      }
    ]
  },

  // Environment variables
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:8080',
  }
}

module.exports = nextConfig