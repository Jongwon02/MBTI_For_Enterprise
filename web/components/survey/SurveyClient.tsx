"use client";

import dynamic from "next/dynamic";

// 응답을 브라우저 저장소에서 읽고 로그인 상태를 확인하므로 서버에서 렌더링하지 않는다.
export const SurveyClient = dynamic(() => import("./DiagnosisEntry").then((m) => m.DiagnosisEntry), {
  ssr: false,
  loading: () => (
    <div className="survey-body"><div className="survey-wrap single"><div className="panel loading-panel">진단 화면을 준비하는 중입니다…</div></div></div>
  ),
});
