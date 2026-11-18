"use client";

import { useEffect, useState } from "react";
import { getMe } from "./api";
import { useAuth } from "./auth";

// 사용자별로 한 번만 묻는다(헤더가 페이지마다 다시 그려지므로). 화면 표시용이며, 권한은 서버가 요청마다 확인한다.
const cache = new Map<string, Promise<boolean>>();

function checkAdmin(userId: string): Promise<boolean> {
  let p = cache.get(userId);
  if (!p) {
    p = getMe().then((me) => me.is_admin === true).catch(() => {
      cache.delete(userId); // 실패하면 다음에 다시 묻는다
      return false;
    });
    cache.set(userId, p);
  }
  return p;
}

/** 관리자 메뉴를 보일지. 로그인 확인 전·확인 중에는 null. */
export function useIsAdmin(): boolean | null {
  const auth = useAuth();
  const userId = auth.status === "signed-in" ? auth.user.id : null;
  const [result, setResult] = useState<{ userId: string; admin: boolean } | null>(null);

  useEffect(() => {
    if (!userId) return;
    let alive = true;
    checkAdmin(userId).then((admin) => {
      if (alive) setResult({ userId, admin });
    });
    return () => {
      alive = false;
    };
  }, [userId]);

  if (auth.status === "signed-out") return false;
  if (!userId || result?.userId !== userId) return null;
  return result.admin;
}
