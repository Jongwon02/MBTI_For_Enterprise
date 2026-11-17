// API(engine/bizdna) 응답·설문 구조의 타입. 원본 정의는 engine/bizdna/config/*.json과 engine.py.

export type Score = 1 | 2 | 3 | 4 | 5;
export type PlanValue = string | number | string[] | null;

export interface Survey {
  company: Record<string, string | number | string[] | null>;
  answers: {
    dna: Record<string, number>;
    stage: Record<string, number>;
    competence: Record<string, number>;
    plan: Record<string, PlanValue>;
  };
}

export interface Option { value: string; label: string }

export interface CompanyField {
  key: string; label: string; type: "text" | "select" | "number" | "multi" | "textarea";
  required?: boolean; options?: string[]; unit?: string; min?: number; max?: number; step?: number; placeholder?: string;
}

export interface PlanItem {
  code: string; phase: "basic" | "full"; title: string; type: "multi" | "single" | "number";
  max?: number; required?: boolean; unit?: string; min?: number; step?: number; help?: string; options?: Option[];
}

export interface Questions {
  version: string;
  scale5: string[];
  company_fields: CompanyField[];
  dna: {
    prompt: string; scale: string[];
    axes: { key: string; name: string; left: string; right: string; caption: string }[];
    items: { code: string; axis: string; left: string; right: string }[];
  };
  stage: { draft: boolean; prompt: string; items: { key: string; title: string; levels: string[] }[] };
  competence: { prompt: string; domains: { code: string; title: string; caption: string; items: { code: string; text: string }[] }[] };
  plan: { draft: boolean; items: PlanItem[] };
}

export interface Axis {
  key: string; score: number | null; letter: string | null; boundary: boolean | null;
  tendency?: string; a?: string; b?: string; answered: number; low_reliability: boolean;
}

export interface Strategy {
  code: string; name: string; score: number; status: "recommended" | "deferred";
  factors: { fit: number; urgency: number; impact: number; feasibility: number };
  matched_goals: string[]; reasons: string[]; applied_rules: string[]; actions: string[]; kpis: string[];
}

export interface DiagnosisResult {
  model_version: string;
  questions_version: string;
  mode: "basic" | "full";
  company: Record<string, unknown>;
  dna: {
    type: string; name: string | null; complete: boolean; missing: string[];
    profile: { name: string; traits: string; strategy: string } | null;
    axes: Record<string, Axis>;
  };
  competence: {
    domains: Record<string, number | null>; names: Record<string, string>; total: number;
    grade: { grade: string; name: string; meaning: string }; missing: string[]; missing_ratio: number;
  } | null;
  stage: {
    code: string | null; level?: number; name?: string; task?: string; weighted_index?: number;
    provisional?: string; gate_adjusted?: boolean; gates_applied?: { id: string; reason: string }[];
    inputs?: Record<string, number>; missing: string[];
  } | null;
  goals: { code: string; name: string }[];
  risks: string[];
  strategies: Strategy[] | null;
  top_recommended: Strategy[] | null;
  limitations: string[];
  completeness: Record<string, unknown>;
}

// ---- 회원 진단 회차 (api/bizdna_api/main.py) ----

export type DiagnosisStatus = "draft" | "basic_completed" | "full_completed";

export interface DiagnosisProgress {
  step: number; maxStep: number; basicDone: boolean; phase: "basic" | "full"; percent: number;
}

export interface DiagnosisSummary {
  id: string;
  company_name: string | null;
  phase: "basic" | "full";
  status: DiagnosisStatus;
  progress: Partial<DiagnosisProgress>;
  model_version: string | null;
  questions_version: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  summary: {
    dna_type: string | null; dna_name: string | null; stage: string | null; stage_name: string | null;
    total: number | null; grade: string | null;
  } | null;
}

export interface DiagnosisRecord extends Omit<DiagnosisSummary, "summary"> {
  survey: Survey;
  result: DiagnosisResult | null;
}
