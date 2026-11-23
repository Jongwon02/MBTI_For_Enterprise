// Supabase 공개 설정. 브라우저에 공개되는 값만 둔다(비밀키는 api 쪽에만). 중소경영과 같은 프로젝트·같은 변수 이름을 쓴다.
export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/** 값이 없으면 회원 기능을 끄고 게스트 진단만 제공한다. */
export const AUTH_ENABLED = Boolean(SUPABASE_URL && SUPABASE_KEY);

/**
 * 로그인 쿠키 이름. 기본 이름(sb-<ref>-auth-token)은 같은 도메인의 중소경영이 쓰므로 따로 둔다(sosang/CLAUDE.md 3.4).
 * 그래야 한쪽의 로그인·로그아웃이 다른 쪽에 영향을 주지 않는다.
 */
export const AUTH_COOKIE = "sb-sosang-auth-token";
