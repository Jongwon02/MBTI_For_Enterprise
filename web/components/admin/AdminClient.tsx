"use client";

import dynamic from "next/dynamic";

// 로그인 상태를 쓰므로 서버에서 렌더링하지 않는다(MyPageClient와 같은 방식).
export const AdminClient = dynamic(() => import("./AdminApp").then((m) => m.AdminApp), {
  ssr: false,
  loading: () => (
    <div className="admin-body"><div className="admin-wrap"><div className="panel loading-panel">불러오는 중입니다…</div></div></div>
  ),
});
