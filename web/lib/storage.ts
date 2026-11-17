import type { Survey } from "./types";

// 진행 중인 응답은 항상 이 브라우저에 자동 저장한다. 게스트는 여기에만, 회원은 서버(진단 회차)에도 저장한다.
const KEY = "bizdna.survey.v1";
const GUEST_KEY = "bizdna.guest";

// 정밀진단 첫 단계 번호: 기업정보(0) + DNA 4축(1~4) + 성장단계(5) + 경영목표(6) 다음. SurveyApp의 buildSteps 순서와 맞춘다.
export const FIRST_FULL_STEP = 7;

export interface SavedSurvey {
  survey: Survey;
  step: number;
  maxStep: number;
  basicDone: boolean;
  phase: "basic" | "full";
  savedAt: string;
  /** 회원 응답이면 작성자와 서버 회차 ID. 게스트 응답에는 없다. */
  userId?: string;
  diagnosisId?: string;
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

/** 게스트로 진단하기를 고른 브라우저인지 */
export function isGuestChosen(): boolean {
  try {
    return window.localStorage.getItem(GUEST_KEY) === "1";
  } catch {
    return false;
  }
}

export function chooseGuest(): void {
  try {
    window.localStorage.setItem(GUEST_KEY, "1");
  } catch {
    // 저장소를 쓸 수 없으면 이번 화면에서만 게스트로 진행한다.
  }
}

/** 응답이 하나라도 있는지(빈 설문인지 판단) */
export function hasAnswers(s: Survey): boolean {
  const a = s.answers;
  return Object.values(s.company).some((v) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0))
    || [a.dna, a.stage, a.competence, a.plan].some((x) => Object.keys(x).length > 0);
}

/** 로그아웃할 때 이 브라우저에 남은 회원 응답을 지운다(공용 PC 대비). 게스트 응답은 남긴다. */
export function clearMemberDraft(): void {
  if (loadSaved()?.userId) clearSaved();
}
