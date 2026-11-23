"use client";

import dynamic from "next/dynamic";
import { loadSaved } from "@/lib/storage";
import { SurveyApp } from "./SurveyApp";

function Entry() {
  return <SurveyApp initial={loadSaved()} />;
}

// 응답을 브라우저 저장소에서 읽으므로 서버에서 렌더링하지 않는다(중소경영과 같은 방식).
export const SurveyClient = dynamic(() => Promise.resolve(Entry), {
  ssr: false,
  loading: () => (
    <div className="survey-body"><div className="survey-wrap single"><div className="panel loading-panel">진단 화면을 준비하는 중입니다…</div></div></div>
  ),
});
