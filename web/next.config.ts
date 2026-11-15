import type { NextConfig } from "next";

// FastAPI 서버 주소. 기본은 로컬 개발 서버.
const API_URL = process.env.BIZDNA_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  // Vercel에서는 vercel.json의 서비스 라우팅이 /api/*를 api 서비스로 보낸다. 이 rewrite는 로컬 개발용이다.
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default nextConfig;
