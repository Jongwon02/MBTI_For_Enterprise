import { accessToken } from "./auth";
import type { AssessmentProgress, AssessmentRecord, AssessmentSummary, DiagnosisResult, Questions, Survey } from "./types";

// /api/sosang/* 요청은 로컬에서는 next.config.ts의 rewrites로 FastAPI(기본 127.0.0.1:8001)에,
// Vercel에서는 vercel.json 서비스 라우팅으로 sosang-api에 전달된다. basePath(/sosang)는 붙지 않는다.
const BASE = "/api/sosang";

export class ApiError extends Error {
  constructor(message: string, public status = 0) {
    super(message);
  }
}

const OFFLINE = "진단 서버에 연결하지 못했습니다. API 서버가 실행 중인지 확인하세요.";

async function request(path: string, init?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError(OFFLINE);
  }
  if (res.ok) return res;
  let detail = `요청 실패 (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // 본문이 JSON이 아니면 상태 코드만 알린다.
  }
  if (res.status >= 500) detail = OFFLINE;
  throw new ApiError(detail, res.status);
}

const json = (survey: Survey): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ survey }),
});

export async function fetchQuestions(): Promise<Questions> {
  return (await request("/questions")).json();
}

export async function runDiagnosis(survey: Survey): Promise<DiagnosisResult> {
  return (await request("/diagnose", json(survey))).json();
}

export async function downloadReport(survey: Survey, storeName: string): Promise<void> {
  const blob = await (await request("/report", json(survey))).blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `소상공인진단_${storeName || "점포"}_기본형.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

// ---- 회원가입·진단 저장. 로그인 토큰을 실어 보내고, 서버가 본인 회차만 돌려준다(sosang/CLAUDE.md 3.4·11장). ----

async function authed(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await accessToken();
  if (!token) throw new ApiError("로그인이 필요합니다.", 401);
  return request(path, {
    ...init,
    headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), Authorization: `Bearer ${token}`, ...init.headers },
  });
}

/** 회원가입(아이디 + 비밀번호, 이메일 인증 없음). 서버가 확인 완료 상태의 소상공인 계정을 만들고, 화면은 이어서 바로 로그인한다. */
export async function createAccount(body: {
  username: string; password: string; name: string; agree_privacy: boolean; agree_storage: boolean; terms_version: string;
}): Promise<void> {
  await request("/auth/signup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

export async function listAssessments(): Promise<AssessmentSummary[]> {
  return (await authed("/assessments")).json();
}

export async function getAssessment(id: string): Promise<AssessmentRecord> {
  return (await authed(`/assessments/${encodeURIComponent(id)}`)).json();
}

/** id가 없으면 새 회차를 만든다. complete면 최종저장(서버가 엔진을 실행해 결과와 버전을 함께 저장). */
export async function saveAssessment(
  id: string | null, survey: Survey, progress: AssessmentProgress, complete = false,
): Promise<AssessmentRecord> {
  const body = JSON.stringify({ survey, progress, complete });
  const res = id
    ? await authed(`/assessments/${encodeURIComponent(id)}`, { method: "PUT", body })
    : await authed("/assessments", { method: "POST", body });
  return res.json();
}

export async function deleteAssessment(id: string): Promise<void> {
  await authed(`/assessments/${encodeURIComponent(id)}`, { method: "DELETE" });
}
