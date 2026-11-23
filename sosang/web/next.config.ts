import type { NextConfig } from "next";

// 소상공인 FastAPI 서버 주소. 기본은 로컬 개발 서버(중소경영 8000과 겹치지 않게 8001).
const API_URL = process.env.SOSANG_API_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  // 같은 도메인에서 중소경영과 합칠 때 겹치지 않게 모든 화면을 /sosang 아래에 둔다(sosang/CLAUDE.md 3.3).
  basePath: "/sosang",
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
  // Vercel에서는 vercel.json 서비스 라우팅이 /api/sosang/*를 sosang-api로 보낸다. 아래는 로컬 개발용이다.
  // basePath: false가 없으면 /sosang/api/sosang/*로 바뀐다(Next.js rewrites 문서).
  async rewrites() {
    if (process.env.VERCEL) return [];
    return [{ source: "/api/sosang/:path*", destination: `${API_URL}/api/sosang/:path*`, basePath: false }];
  },
  // 단독 개발 중에는 루트(/)를 소상공인 홈으로 보낸다. 통합 후 루트는 두 진단의 선택 화면이 된다(9장).
  async redirects() {
    if (process.env.VERCEL) return [];
    return [{ source: "/", destination: "/sosang", permanent: false, basePath: false }];
  },
};

export default nextConfig;
