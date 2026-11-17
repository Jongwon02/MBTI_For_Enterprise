"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, createAccount } from "@/lib/api";
import { authErrorMessage, safeNext } from "@/lib/auth";
import { AUTH_ENABLED } from "@/lib/supabase/config";
import { supabaseBrowser } from "@/lib/supabase/client";

// 동의 문구 버전. 문구를 바꾸면 값을 바꾼다(가입 시 consents 테이블에 함께 기록됨).
const TERMS_VERSION = "2026-11-17-draft";

export function SignupForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [privacy, setPrivacy] = useState(false);
  const [storage, setStorage] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 8) return setError("비밀번호는 8자 이상이어야 합니다.");
    if (password !== confirm) return setError("비밀번호 확인이 일치하지 않습니다.");
    if (!privacy || !storage) return setError("필수 동의 항목에 동의해야 가입할 수 있습니다.");
    const sb = supabaseBrowser();
    if (!sb) return;
    setBusy(true);
    try {
      // 이메일 인증 없이 가입(서버가 확인 완료 계정을 만든다) → 바로 로그인
      await createAccount({
        email: email.trim(), password, name: name.trim(),
        agree_privacy: privacy, agree_storage: storage, terms_version: TERMS_VERSION,
      });
    } catch (err) {
      setBusy(false);
      return setError(err instanceof ApiError ? err.message : "가입을 처리하지 못했습니다.");
    }
    const { error: loginError } = await sb.auth.signInWithPassword({ email: email.trim(), password });
    setBusy(false);
    if (loginError) {
      // 계정은 만들어졌으므로 로그인 화면으로 보낸다.
      setError(`가입은 완료되었습니다. 로그인 화면에서 다시 로그인해 주세요. (${authErrorMessage(loginError.message)})`);
      return;
    }
    router.replace(safeNext("/mypage"));
    router.refresh();
  };

  return (
    <div className="auth-card panel">
      <h2>회원가입</h2>
      <p className="muted">이메일 인증 없이 바로 가입됩니다. 가입하면 진단을 중간저장하고 다른 기기에서도 이어 할 수 있으며, 최종저장한 진단 결과를 마이페이지에서 다시 볼 수 있습니다.</p>
      {!AUTH_ENABLED && <p className="warn-box" role="status">회원 기능을 준비 중입니다. 지금은 게스트로 진단할 수 있습니다.</p>}
      <form className="auth-form" onSubmit={submit}>
        <label>
          <span>이름 (담당자)</span>
          <input autoComplete="name" required maxLength={40} value={name} onChange={(e) => setName(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        <label>
          <span>이메일</span>
          <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        <label>
          <span>비밀번호 <small>8자 이상</small></span>
          <input type="password" autoComplete="new-password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        <label>
          <span>비밀번호 확인</span>
          <input type="password" autoComplete="new-password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} disabled={!AUTH_ENABLED} />
        </label>
        <fieldset className="consent-box">
          <legend>약관 동의</legend>
          <label className="check">
            <input type="checkbox" checked={privacy} onChange={(e) => setPrivacy(e.target.checked)} />
            <span><b>[필수]</b> 개인정보 수집·이용 동의 — 이름·이메일을 회원 식별과 로그인에 사용하며, 탈퇴 시 삭제합니다.</span>
          </label>
          <label className="check">
            <input type="checkbox" checked={storage} onChange={(e) => setStorage(e.target.checked)} />
            <span><b>[필수]</b> 진단결과 저장 동의 — 입력한 기업정보·응답·진단결과를 내 계정에 저장해 마이페이지에서 보여줍니다.</span>
          </label>
          <p className="auth-note">동의 문구는 초안입니다. 개인정보처리방침이 확정되면 바뀔 수 있습니다.</p>
        </fieldset>
        {error && <p className="error-text" role="alert">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={busy || !AUTH_ENABLED}>{busy ? "가입 중…" : "가입하기"}</button>
      </form>
      <div className="auth-links">
        <span>이미 회원이신가요? <Link href="/login">로그인</Link></span>
      </div>
    </div>
  );
}
