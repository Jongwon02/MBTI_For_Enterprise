import { accessToken } from "./auth";
import type { AdminFactDetail, AdminFactPage, AdminFilters, AdminOverview } from "./admin-types";
import type { DiagnosisProgress, DiagnosisRecord, DiagnosisResult, DiagnosisSummary, Questions, Survey } from "./types";

// /api/* 요청은 next.config.ts의 rewrites로 FastAPI 서버(기본 127.0.0.1:8000)에 전달된다.

export class ApiError extends Error {
  constructor(message: string, public status = 0) {
    super(message);
  }
}

async function handle(res: Response): Promise<Response> {
  if (res.ok) return res;
  let detail = `요청 실패 (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // 본문이 JSON이 아니면 상태 코드만 알린다.
  }
  if (res.status >= 500 && res.status !== 503) detail = "진단 서버에 연결하지 못했습니다. API 서버가 실행 중인지 확인하세요.";
  throw new ApiError(detail, res.status);
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

// ---- 회원 진단 저장 (FR-01, FR-12). 로그인 토큰을 실어 보내고, 서버가 본인 회차만 돌려준다. ----

async function authed(path: string, init: RequestInit = {}): Promise<Response> {
  const token = await accessToken();
  if (!token) throw new ApiError("로그인이 필요합니다.", 401);
  return request(path, {
    ...init,
    headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), Authorization: `Bearer ${token}`, ...init.headers },
  });
}

export async function listDiagnoses(): Promise<DiagnosisSummary[]> {
  return (await authed("/api/diagnoses")).json();
}

export async function getDiagnosis(id: string): Promise<DiagnosisRecord> {
  return (await authed(`/api/diagnoses/${encodeURIComponent(id)}`)).json();
}

/** id가 없으면 새 회차를 만든다. complete를 주면 최종저장(서버가 엔진을 실행해 결과를 함께 저장). */
export async function saveDiagnosis(
  id: string | null, survey: Survey, progress: DiagnosisProgress, complete?: "basic" | "full",
): Promise<DiagnosisRecord> {
  const body = JSON.stringify({ survey, progress, complete: complete ?? null });
  const res = id
    ? await authed(`/api/diagnoses/${encodeURIComponent(id)}`, { method: "PUT", body })
    : await authed("/api/diagnoses", { method: "POST", body });
  return res.json();
}

export async function deleteDiagnosis(id: string): Promise<void> {
  await authed(`/api/diagnoses/${encodeURIComponent(id)}`, { method: "DELETE" });
}

/** 회원가입(아이디 + 비밀번호, 이메일 인증 없음). 서버가 확인 완료 상태의 계정을 만들고, 화면은 이어서 바로 로그인한다. */
export async function createAccount(body: {
  username: string; password: string; name: string;
  agree_privacy: boolean; agree_storage: boolean; agree_analytics: boolean; terms_version: string;
}): Promise<void> {
  await request("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ---- 내 정보·관리자 (docs/admin.md). 관리자 API는 서버가 요청마다 관리자인지 다시 확인한다. ----

export async function getMe(): Promise<{ id: string; is_admin: boolean }> {
  return (await authed("/api/me")).json();
}

function adminQuery(filters: AdminFilters, extra: Record<string, string | number> = {}): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries({ ...filters, ...extra })) if (v !== "" && v != null) q.set(k, String(v));
  const s = q.toString();
  return s ? `?${s}` : "";
}

export async function adminOverview(filters: AdminFilters): Promise<AdminOverview> {
  return (await authed(`/api/admin/overview${adminQuery(filters)}`)).json();
}

export async function adminFacts(filters: AdminFilters, offset: number, limit: number): Promise<AdminFactPage> {
  return (await authed(`/api/admin/facts${adminQuery(filters, { offset, limit })}`)).json();
}

export async function adminFact(id: string): Promise<AdminFactDetail> {
  return (await authed(`/api/admin/facts/${encodeURIComponent(id)}`)).json();
}

export async function adminExportCsv(filters: AdminFilters): Promise<void> {
  const blob = await (await authed(`/api/admin/export.csv${adminQuery(filters)}`)).blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bizdna_facts_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}
