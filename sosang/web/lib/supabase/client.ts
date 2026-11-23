"use client";

import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { AUTH_COOKIE, AUTH_ENABLED, SUPABASE_KEY, SUPABASE_URL } from "./config";

let client: SupabaseClient | null = null;

/** 브라우저용 Supabase 클라이언트. 로그인에만 쓴다(데이터는 FastAPI를 거친다, sosang/CLAUDE.md 11장). */
export function supabaseBrowser(): SupabaseClient | null {
  if (!AUTH_ENABLED) return null;
  client ??= createBrowserClient(SUPABASE_URL, SUPABASE_KEY, { cookieOptions: { name: AUTH_COOKIE, path: "/" } });
  return client;
}
