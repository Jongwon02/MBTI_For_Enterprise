"use client";

import dynamic from "next/dynamic";

// 로그인 상태와 브라우저 저장소를 쓰므로 서버에서 렌더링하지 않는다.
export const MyPageClient = dynamic(() => import("./MyPageApp").then((m) => m.MyPageApp), {
  ssr: false,
  loading: () => (
    <div className="mypage-body"><div className="mypage-wrap"><div className="panel loading-panel">불러오는 중입니다…</div></div></div>
  ),
});
