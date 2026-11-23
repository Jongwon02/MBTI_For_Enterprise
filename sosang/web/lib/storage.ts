import type { Survey } from "./types";

// 진행 중인 응답은 이 브라우저에만 저장한다(게스트). 키는 sosang. 접두어(중소경영 bizdna.* 와 같은 출처에서 섞이지 않게, CLAUDE.md 3.3).
const KEY = "sosang.survey.v1";

export interface SavedSurvey {
  survey: Survey;
  step: number;
  maxStep: number;
  done: boolean;
  savedAt: string;
  /** 회원이면 서버에 저장된 회차 ID(sosang.assessments). 게스트는 없다. */
  serverId?: string | null;
}

export function emptySurvey(): Survey {
  return { store: {}, finance: {}, answers: { dna: {}, competence: {}, special: {} }, observations: {}, benchmark: null };
}

export function loadSaved(): SavedSurvey | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as SavedSurvey;
    return { ...data, survey: { ...emptySurvey(), ...data.survey } };
  } catch {
    return null;
  }
}

export function save(data: Omit<SavedSurvey, "savedAt">): string | null {
  const savedAt = new Date().toISOString();
  try {
    window.localStorage.setItem(KEY, JSON.stringify({ ...data, savedAt }));
    return savedAt;
  } catch {
    return null;
  }
}

export function clearSaved(): void {
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    // 저장소를 쓸 수 없는 환경이면 무시한다.
  }
}

/** 로그아웃 때 이 기기의 진행 중 응답을 지운다(소상공인 sosang.* 키만, 중소경영 키는 건드리지 않는다). */
export function clearMemberDraft(): void {
  clearSaved();
}
