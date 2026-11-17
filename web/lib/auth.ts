"use client";

import type { User } from "@supabase/supabase-js";
import { useEffect, useState } from "react";
import { AUTH_ENABLED } from "./supabase/config";
import { supabaseBrowser } from "./supabase/client";

export type AuthState =
  | { status: "loading"; user: null }
  | { status: "signed-out"; user: null }
  | { status: "signed-in"; user: User };

/** 로그인 상태 구독. Supabase가 설정되지 않았으면 항상 signed-out(게스트 전용)이다. */
export function useAuth(): AuthState {
  const [state, setState] = useState<AuthState>(() =>
    AUTH_ENABLED ? { status: "loading", user: null } : { status: "signed-out", user: null },
  );
  useEffect(() => {
    const sb = supabaseBrowser();
    if (!sb) return;
    // INITIAL_SESSION 이벤트가 구독 직후 비동기로 한 번 온다.
    const { data } = sb.auth.onAuthStateChange((_event, session) => {
      setState(session?.user ? { status: "signed-in", user: session.user } : { status: "signed-out", user: null });
    });
    return () => data.subscription.unsubscribe();
  }, []);
  return state;
}

/** API 호출에 실을 access token. 만료가 가까우면 supabase-js가 갱신한 토큰을 준다. */
export async function accessToken(): Promise<string | null> {
  const sb = supabaseBrowser();
  if (!sb) return null;
  const { data } = await sb.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function signOut(): Promise<void> {
  await supabaseBrowser()?.auth.signOut();
}

export function displayName(user: User): string {
  const name = typeof user.user_metadata?.name === "string" ? user.user_metadata.name.trim() : "";
  return name || user.email || "회원";
}

/** 로그인 화면의 next 파라미터. 같은 사이트 경로만 허용한다. */
export function safeNext(fallback = "/mypage"): string {
  const raw = new URLSearchParams(window.location.search).get("next") ?? "";
  return raw.startsWith("/") && !raw.startsWith("//") ? raw : fallback;
}

/** Supabase 오류 메시지를 한국어로 바꾼다. */
export function authErrorMessage(message: string): string {
  const m = message.toLowerCase();
  if (m.includes("invalid login credentials")) return "이메일 또는 비밀번호가 올바르지 않습니다.";
  if (m.includes("email not confirmed")) return "이메일 인증을 아직 마치지 않았습니다. 받은 메일의 인증 링크를 눌러 주세요.";
  if (m.includes("already registered") || m.includes("already been registered")) return "이미 가입된 이메일입니다. 로그인해 주세요.";
  if (m.includes("password") && (m.includes("6 characters") || m.includes("at least") || m.includes("weak")))
    return "비밀번호가 너무 짧거나 쉽습니다. 8자 이상으로 영문·숫자를 섞어 주세요.";
  if (m.includes("rate limit") || m.includes("too many")) return "요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.";
  if (m.includes("invalid") && m.includes("email")) return "이메일 형식을 확인해 주세요.";
  return "처리하지 못했습니다. 잠시 후 다시 시도해 주세요.";
}
