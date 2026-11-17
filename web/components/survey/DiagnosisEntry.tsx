"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getDiagnosis } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { chooseGuest, clearSaved, hasAnswers, isGuestChosen, loadSaved, save, type SavedSurvey } from "@/lib/storage";
import { AUTH_ENABLED } from "@/lib/supabase/config";
import { SurveyApp } from "./SurveyApp";

type View =
  | { kind: "loading" }
  | { kind: "gate" }
  | { kind: "import"; saved: SavedSurvey }
  | { kind: "error"; message: string }
  | { kind: "survey"; initial: SavedSurvey | null };

function Panel({ children }: { children: React.ReactNode }) {
  return <div className="survey-body"><div className="survey-wrap single">{children}</div></div>;
}

/** 진단 시작 화면. 로그인·회원가입·게스트 중 하나를 고르게 하고, 회원이면 저장된 회차를 이어서 연다. */
export function DiagnosisEntry() {
  const auth = useAuth();
  const userId = auth.user?.id ?? null;
  const [params] = useState(() => new URLSearchParams(window.location.search));
  const [local] = useState(loadSaved);
  const [choice, setChoice] = useState<View | null>(null); // 화면에서 고른 것(게스트·가져오기 등)
  const [loaded, setLoaded] = useState<View | null>(null); // 서버에서 불러온 회차
  const id = params.get("id");
  const minStep = Number(params.get("step")) || 0;

  // 마이페이지에서 "이어하기": 서버 회차를 브라우저 저장으로 옮겨 연다.
  useEffect(() => {
    if (auth.status !== "signed-in" || !id) return;
    let cancelled = false;
    getDiagnosis(id).then((rec) => {
      const p = rec.progress ?? {};
      const saved: SavedSurvey = {
        // 결과 화면의 "정밀진단 계속하기"는 step=정밀진단 첫 단계를 넘긴다.
        survey: rec.survey, step: Math.max(p.step ?? 0, minStep), maxStep: Math.max(p.maxStep ?? 0, minStep), basicDone: p.basicDone ?? rec.status !== "draft",
        phase: p.phase ?? rec.phase, savedAt: rec.updated_at, userId: auth.user.id, diagnosisId: rec.id,
      };
      save(saved);
      if (!cancelled) setLoaded({ kind: "survey", initial: saved });
    }).catch((e) => {
      if (!cancelled) setLoaded({ kind: "error", message: e instanceof ApiError ? e.message : "진단을 불러오지 못했습니다." });
    });
    return () => { cancelled = true; };
  }, [auth, id, minStep]);

  const view: View = (() => {
    if (choice) return choice;
    if (auth.status === "loading") return { kind: "loading" };
    if (auth.status === "signed-out") {
      // 다른 회원이 이 브라우저에 남긴 응답은 게스트에게 보여주지 않는다.
      const guestSaved = local && !local.userId ? local : null;
      return !AUTH_ENABLED || isGuestChosen() || guestSaved ? { kind: "survey", initial: guestSaved } : { kind: "gate" };
    }
    if (id) return loaded ?? { kind: "loading" };
    if (params.get("new")) return { kind: "survey", initial: null };
    if (local?.userId === userId) return { kind: "survey", initial: local };
    if (local && !local.userId && hasAnswers(local.survey)) return { kind: "import", saved: local };
    return { kind: "survey", initial: null };
  })();

  // 주소의 id/new는 한 번만 쓰고 지운다(새로고침 때 다시 불러오지 않도록). "새 진단"이면 이전 응답도 지운다.
  useEffect(() => {
    if (view.kind !== "survey" || !(params.get("id") || params.get("new"))) return;
    if (params.get("new")) clearSaved();
    window.history.replaceState(null, "", "/diagnosis");
  }, [view.kind, params]);

  if (view.kind === "loading") return <Panel><div className="panel loading-panel">진단 화면을 준비하는 중입니다…</div></Panel>;

  if (view.kind === "error") {
    return (
      <Panel>
        <div className="panel notice-panel" role="alert">
          <h3>진단을 불러오지 못했습니다</h3>
          <p>{view.message}</p>
          <Link className="btn btn-dark btn-sm" href="/mypage">마이페이지로</Link>
        </div>
      </Panel>
    );
  }

  if (view.kind === "gate") {
    const next = encodeURIComponent("/diagnosis");
    return (
      <Panel>
        <div className="panel start-gate">
          <span className="step-kicker">시작하기</span>
          <h2>어떻게 진단을 시작할까요?</h2>
          <p className="muted">회원으로 진단하면 응답과 결과가 내 계정에 저장되어 다른 기기에서도 이어 하고, 마이페이지에서 지난 진단을 다시 볼 수 있습니다.</p>
          <div className="gate-options">
            <Link className="gate-option primary" href={`/login?next=${next}`}>
              <b>로그인</b><span>이미 회원이면 로그인하고 시작합니다.</span>
            </Link>
            <Link className="gate-option" href={`/signup?next=${next}`}>
              <b>회원가입</b><span>이메일로 가입하고 진단 결과를 계정에 저장합니다.</span>
            </Link>
            <button className="gate-option" onClick={() => { chooseGuest(); setChoice({ kind: "survey", initial: null }); }}>
              <b>게스트로 진단하기</b><span>가입 없이 바로 시작합니다. 응답은 이 브라우저에만 저장되고 마이페이지는 쓸 수 없습니다.</span>
            </button>
          </div>
        </div>
      </Panel>
    );
  }

  if (view.kind === "import") {
    return (
      <Panel>
        <div className="panel notice-panel">
          <h3>게스트로 진행한 응답이 있습니다</h3>
          <p>
            이 브라우저에 로그인 전에 작성한 응답{view.saved.survey.company.name ? `(${view.saved.survey.company.name})` : ""}이 남아 있습니다.
            내 계정으로 가져오면 이어서 진단하고 마이페이지에 저장됩니다.
          </p>
          <div className="warn-actions">
            <button className="btn btn-primary btn-sm" onClick={() => {
              const saved = { ...view.saved, userId: userId!, diagnosisId: undefined };
              save(saved);
              setChoice({ kind: "survey", initial: saved });
            }}>내 계정으로 가져오기</button>
            <button className="btn btn-line btn-sm" onClick={() => { clearSaved(); setChoice({ kind: "survey", initial: null }); }}>지우고 새로 시작</button>
          </div>
        </div>
      </Panel>
    );
  }

  return (
    <>
      {auth.status === "signed-out" && AUTH_ENABLED && (
        <div className="guest-banner">
          게스트로 진단 중입니다. 응답은 이 브라우저에만 저장됩니다.{" "}
          <Link href="/login?next=%2Fdiagnosis">로그인</Link> 또는 <Link href="/signup?next=%2Fdiagnosis">회원가입</Link>하면 내 계정으로 가져올 수 있습니다.
        </div>
      )}
      <SurveyApp key={view.initial?.diagnosisId ?? "local"} initial={view.initial} member={userId ? { userId } : null} />
    </>
  );
}
