"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getAssessment } from "@/lib/api";
import { clearSaved, loadSaved, type SavedSurvey } from "@/lib/storage";
import { SurveyApp } from "./SurveyApp";

const shell = (body: React.ReactNode) => <div className="survey-body"><div className="survey-wrap single">{body}</div></div>;

/** 마이페이지에서 고른 회원 회차(?id=)를 서버에서 불러온다. */
function ServerEntry({ id }: { id: string }) {
  const [initial, setInitial] = useState<SavedSurvey | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getAssessment(id)
      .then((r) => setInitial({
        survey: r.survey, step: r.progress?.step ?? 0, maxStep: r.progress?.maxStep ?? 0,
        done: false, savedAt: r.updated_at, serverId: r.id,
      }))
      .catch((e) => setError(e instanceof ApiError ? e.message : "저장한 진단을 불러오지 못했습니다."));
  }, [id]);
  if (error) {
    return shell(
      <div className="panel notice-panel" role="alert">
        <h3>저장한 진단을 불러오지 못했습니다</h3>
        <p>{error}</p>
        <div className="warn-actions">
          <Link className="btn btn-dark btn-sm" href="/mypage">마이페이지로</Link>
          <Link className="btn btn-line btn-sm" href="/login?next=%2Fmypage">로그인</Link>
        </div>
      </div>,
    );
  }
  if (!initial) return shell(<div className="panel loading-panel">저장한 진단을 불러오는 중입니다…</div>);
  return <SurveyApp initial={initial} />;
}

function Entry() {
  // 첫 렌더에서 한 번만 정한다(다시 렌더링될 때 저장 내용을 또 지우지 않게).
  const [start] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (id) return { id, initial: null };
    // 마이페이지의 "새 진단 시작": 이 기기의 진행 중 응답을 비우고 새 회차로 시작한다.
    if (params.get("new") === "1") {
      clearSaved();
      return { id: null, initial: null };
    }
    return { id: null, initial: loadSaved() };
  });
  return start.id ? <ServerEntry id={start.id} /> : <SurveyApp initial={start.initial} />;
}

// 응답을 브라우저 저장소에서 읽으므로 서버에서 렌더링하지 않는다(중소경영과 같은 방식).
export const SurveyClient = dynamic(() => Promise.resolve(Entry), {
  ssr: false,
  loading: () => shell(<div className="panel loading-panel">진단 화면을 준비하는 중입니다…</div>),
});
