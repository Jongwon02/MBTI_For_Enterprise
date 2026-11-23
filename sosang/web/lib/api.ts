import type { DiagnosisResult, Questions, Survey } from "./types";

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
