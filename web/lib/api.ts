import type { DiagnosisResult, Questions, Survey } from "./types";

// /api/* 요청은 next.config.ts의 rewrites로 FastAPI 서버(기본 127.0.0.1:8000)에 전달된다.

export class ApiError extends Error {}

async function handle(res: Response): Promise<Response> {
  if (res.ok) return res;
  let detail = `요청 실패 (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // 본문이 JSON이 아니면 상태 코드만 알린다.
  }
  if (res.status >= 500) detail = "진단 서버에 연결하지 못했습니다. API 서버가 실행 중인지 확인하세요.";
  throw new ApiError(detail);
}

async function request(input: string, init?: RequestInit): Promise<Response> {
  try {
    return await handle(await fetch(input, init));
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError("진단 서버에 연결하지 못했습니다. API 서버가 실행 중인지 확인하세요.");
  }
}

export async function fetchQuestions(): Promise<Questions> {
  return (await request("/api/questions")).json();
}

export async function runDiagnosis(survey: Survey, phase: "basic" | "full"): Promise<DiagnosisResult> {
  const res = await request("/api/diagnose", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ survey, phase }),
  });
  return res.json();
}

export async function downloadReport(survey: Survey, mode: "basic" | "advanced", companyName: string): Promise<void> {
  const res = await request("/api/report", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ survey, mode }),
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `BizDNA_${companyName || "기업"}_${mode === "basic" ? "기본형" : "정밀형"}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}
