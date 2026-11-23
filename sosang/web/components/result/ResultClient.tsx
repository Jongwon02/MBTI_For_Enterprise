"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getAssessment } from "@/lib/api";
import { loadSaved } from "@/lib/storage";
import type { AssessmentRecord } from "@/lib/types";
import { ResultApp } from "./ResultApp";

const shell = (body: React.ReactNode) => <div className="result-body"><div className="result-wrap">{body}</div></div>;

/** 회원이 최종저장한 회차(?id=)를 서버에서 불러온다. 본인 회차만 열린다(서버가 확인). */
function ServerResult({ id }: { id: string }) {
  const [rec, setRec] = useState<AssessmentRecord | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    getAssessment(id).then(setRec).catch((e) => setError(e instanceof ApiError ? e.message : "진단 결과를 불러오지 못했습니다."));
  }, [id]);
  if (error) {
    return shell(
      <div className="panel notice-panel" role="alert">
        <h3>진단 결과를 불러오지 못했습니다</h3>
        <p>{error}</p>
        <div className="warn-actions">
          <Link className="btn btn-dark btn-sm" href="/mypage">마이페이지로</Link>
          <Link className="btn btn-line btn-sm" href="/login?next=%2Fmypage">로그인</Link>
        </div>
      </div>,
    );
  }
  if (!rec) return shell(<div className="panel loading-panel">진단 결과를 불러오는 중입니다…</div>);
  if (rec.status !== "completed" || !rec.result) {
    return shell(
      <div className="panel notice-panel">
        <h3>아직 완료하지 않은 진단입니다</h3>
        <p>마지막 단계에서 최종저장하면 결과를 볼 수 있습니다.</p>
        <Link className="btn btn-primary btn-sm" href={`/diagnosis?id=${rec.id}`}>이어서 진단하기</Link>
      </div>,
    );
  }
  return <ResultApp saved={{ survey: rec.survey, step: 0, maxStep: 0, done: true, savedAt: rec.updated_at, serverId: rec.id }} stored={rec.result} />;
}

function Entry() {
  const [id] = useState(() => new URLSearchParams(window.location.search).get("id"));
  const [saved] = useState(() => (id ? null : loadSaved()));
  return id ? <ServerResult id={id} /> : <ResultApp saved={saved} />;
}

// 응답을 브라우저 저장소·로그인 토큰으로 읽으므로 서버에서 렌더링하지 않는다.
export const ResultClient = dynamic(() => Promise.resolve(Entry), {
  ssr: false,
  loading: () => shell(<div className="panel loading-panel">불러오는 중입니다…</div>),
});
