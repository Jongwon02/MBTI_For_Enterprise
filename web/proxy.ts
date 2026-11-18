import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { AUTH_ENABLED, SUPABASE_KEY, SUPABASE_URL } from "@/lib/supabase/config";

// 만료된 Supabase 세션을 갱신해 쿠키에 다시 쓰고, 마이페이지는 로그인한 사용자만 들어오게 한다.
// 실제 권한 검사는 API(FastAPI)가 매 요청 토큰을 검증해 한다. 여기서는 화면 이동만 막는다.
export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });
  if (!AUTH_ENABLED) return response;

  const supabase = createServerClient(SUPABASE_URL, SUPABASE_KEY, {
    cookies: {
      getAll: () => request.cookies.getAll(),
      setAll: (list, headers) => {
        list.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        list.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
        Object.entries(headers ?? {}).forEach(([k, v]) => response.headers.set(k, v));
      },
    },
  });

  const { data } = await supabase.auth.getClaims();
  // 로그인이 필요한 화면. 관리자 여부는 화면과 API가 따로 확인한다(docs/admin.md).
  const protectedPath = ["/mypage", "/admin"].some((p) => request.nextUrl.pathname.startsWith(p));
  if (!data?.claims && protectedPath) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(request.nextUrl.pathname)}`;
    return NextResponse.redirect(url);
  }
  return response;
}

export const config = {
  // 정적 파일과 API(FastAPI로 넘어감)는 건너뛴다.
  matcher: ["/((?!api/|_next/static|_next/image|favicon.ico|.*\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)"],
};
