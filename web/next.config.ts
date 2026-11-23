import type { NextConfig } from "next";

// FastAPI 서버 주소. 기본은 로컬 개발 서버.
const API_URL = process.env.BIZDNA_API_URL ?? "http://127.0.0.1:8000";
// 소상공인 앱(sosang/web, basePath /sosang)과 API 주소. 로컬에서 3000 하나로 두 진단을 같이 보려고 넘긴다.
const SOSANG_WEB_URL = process.env.SOSANG_WEB_URL ?? "http://127.0.0.1:3001";
const SOSANG_API_URL = process.env.SOSANG_API_URL ?? "http://127.0.0.1:8001";

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
  // Vercel에서는 vercel.json의 서비스 라우팅이 /api/sosang/*·/sosang/*·/api/*를 각 서비스로 보낸다. 이 rewrite는 로컬 개발용이다.
  // 소상공인 규칙을 /api/:path*보다 앞에 둔다(vercel.json과 같은 순서).
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [
      { source: "/api/sosang/:path*", destination: `${SOSANG_API_URL}/api/sosang/:path*` },
      { source: "/sosang", destination: `${SOSANG_WEB_URL}/sosang` },
      { source: "/sosang/:path*", destination: `${SOSANG_WEB_URL}/sosang/:path*` },
      { source: "/api/:path*", destination: `${API_URL}/api/:path*` },
    ];
  },
};

export default nextConfig;
