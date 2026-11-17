// Supabase 공개 설정. 브라우저에 공개되는 값만 둔다(비밀키는 api 쪽에만).
// Vercel의 Supabase 연동이 등록하는 이름을 쓰고, 구형 연동의 anon key 이름도 받는다.
export const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
export const SUPABASE_KEY =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

/** 값이 없으면 회원 기능을 끄고 게스트 진단만 제공한다. */
export const AUTH_ENABLED = Boolean(SUPABASE_URL && SUPABASE_KEY);
