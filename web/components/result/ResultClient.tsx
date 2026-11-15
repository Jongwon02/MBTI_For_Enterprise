"use client";

import dynamic from "next/dynamic";

// 응답을 브라우저 저장소에서 읽으므로 서버에서 렌더링하지 않는다.
export const ResultClient = dynamic(() => import("./ResultApp").then((m) => m.ResultApp), {
  ssr: false,
  loading: () => (
    <div className="result-body"><div className="result-wrap"><div className="panel loading-panel">불러오는 중입니다…</div></div></div>
  ),
});
