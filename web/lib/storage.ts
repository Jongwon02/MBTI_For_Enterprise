import type { Survey } from "./types";

// 계정·DB(FR-01, FR-12)가 생기기 전까지 응답은 이 브라우저에만 저장한다.
const KEY = "bizdna.survey.v1";

// 정밀진단 첫 단계 번호: 기업정보(0) + DNA 4축(1~4) + 성장단계(5) + 경영목표(6) 다음. SurveyApp의 buildSteps 순서와 맞춘다.
export const FIRST_FULL_STEP = 7;

export interface SavedSurvey {
  survey: Survey;
  step: number;
  maxStep: number;
  basicDone: boolean;
  phase: "basic" | "full";
  savedAt: string;
}

export function emptySurvey(): Survey {
  return { company: {}, answers: { dna: {}, stage: {}, competence: {}, plan: {} } };
}

export function loadSaved(): SavedSurvey | null {
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as SavedSurvey) : null;
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
