"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authErrorMessage, safeNext } from "@/lib/auth";
import { chooseGuest } from "@/lib/storage";
import { AUTH_ENABLED } from "@/lib/supabase/config";
import { supabaseBrowser } from "@/lib/supabase/client";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const sb = supabaseBrowser();
    if (!sb) return;
    setBusy(true);
    setError(null);
    const { error: err } = await sb.auth.signInWithPassword({ email: email.trim(), password });
    setBusy(false);
    if (err) {
      setError(authErrorMessage(err.message));
      return;
    }
    router.replace(safeNext());
    router.refresh();
  };

  const guest = () => {
    chooseGuest();
    router.push("/diagnosis");
  };

  // 가입 화면으로 갈 때 next(돌아갈 곳)를 그대로 넘긴다.
  const toSignup = () => router.push(`/signup${window.location.search}`);

  return (
    <div className="auth-card panel">
      <h2>로그인</h2>
      <p className="muted">진단 응답과 결과를 내 계정에 저장하고 마이페이지에서 다시 볼 수 있습니다.</p>
      {!AUTH_ENABLED && <p className="warn-box" role="status">회원 기능을 준비 중입니다. 지금은 게스트로 진단할 수 있습니다.</p>}
      <form className="auth-form" onSubmit={submit}>
        <label>
          <span>이메일</span>
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        <label>
          <span>비밀번호</span>
          <input type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        {error && <p className="error-text" role="alert">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={busy || !AUTH_ENABLED}>{busy ? "로그인 중…" : "로그인"}</button>
      </form>
      <div className="auth-links">
        <span>아직 회원이 아니신가요? <button type="button" className="text-btn" onClick={toSignup}>회원가입</button></span>
        <Link className="text-btn" href="/">처음으로</Link>
      </div>
      <div className="auth-divider"><span>또는</span></div>
      <button className="btn btn-line" type="button" onClick={guest}>게스트로 진단하기</button>
      <p className="auth-note">게스트 응답은 이 브라우저에만 저장됩니다. 나중에 가입하면 내 계정으로 가져올 수 있습니다.</p>
    </div>
  );
}
