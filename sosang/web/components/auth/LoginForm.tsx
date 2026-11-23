"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { authErrorMessage, isSosangUser, normalizeUsername, safeNext, USERNAME_RE, usernameToEmail } from "@/lib/auth";
import { AUTH_ENABLED } from "@/lib/supabase/config";
import { supabaseBrowser } from "@/lib/supabase/client";

// 중소경영 components/auth/LoginForm.tsx를 복사해 고쳤다. 소상공인 계정(@users.sosang.invalid)으로만 로그인한다.
export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const sb = supabaseBrowser();
    if (!sb) return;
    setError(null);
    // 형식이 틀린 아이디는 가입될 수 없으므로 서버에 묻지 않고 같은 안내를 보여준다.
    if (!USERNAME_RE.test(normalizeUsername(username))) return setError("아이디 또는 비밀번호가 올바르지 않습니다.");
    setBusy(true);
    const { data, error: err } = await sb.auth.signInWithPassword({ email: usernameToEmail(username), password });
    if (!err && !isSosangUser(data.user)) {
      // 서비스 표시가 없는 계정(관리자 API를 거치지 않고 만든 계정)은 받지 않는다.
      await sb.auth.signOut({ scope: "local" });
      setBusy(false);
      return setError("소상공인 진단 회원이 아닙니다. 회원가입 후 이용해 주세요.");
    }
    setBusy(false);
    if (err) return setError(authErrorMessage(err.message));
    router.replace(safeNext());
    router.refresh();
  };

  // 가입 화면으로 갈 때 next(돌아갈 곳)를 그대로 넘긴다.
  const toSignup = () => router.push(`/signup${window.location.search}`);

  return (
    <div className="auth-card panel">
      <h2>로그인</h2>
      <p className="muted">진단 응답과 결과를 내 계정에 저장하고 마이페이지에서 다시 볼 수 있습니다. 중소기업 진단 계정과는 별도입니다.</p>
      {!AUTH_ENABLED && <p className="warn-box" role="status">회원 기능을 준비 중입니다. 지금은 게스트로 진단할 수 있습니다.</p>}
      <form className="auth-form" onSubmit={submit}>
        <label>
          <span>아이디</span>
          <input autoComplete="username" autoCapitalize="none" spellCheck={false} required maxLength={20} value={username} onChange={(e) => setUsername(e.target.value)} disabled={!AUTH_ENABLED} />
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
      <Link className="btn btn-line" href="/diagnosis">게스트로 진단하기</Link>
      <p className="auth-note">게스트 응답은 이 브라우저에만 저장됩니다. 진단 중에 가입·로그인하면 그 응답을 내 계정에 이어서 저장합니다.</p>
    </div>
  );
}
