// API(/api/sosang/*) 응답 형태. 정본은 sosang/api/engine/sosang/engine.py와 config/*.json이다.

export type Likert = 1 | 2 | 3 | 4 | 5;

export interface DnaItem { code: string; axis: string; left: string; right: string }
export interface CompetenceItem { code: string; area: string; text: string }
export interface SpecialItem extends CompetenceItem { sector: string }

export interface Area { code: string; name: string; detail: string }
export interface DnaAxisMeta { key: string; name: string; a: string; b: string; a_name: string; b_name: string; items: string[] }

export interface Industries {
  version: string;
  draft: boolean;
  majors: { code: string; name: string; sector_group: string; examples: string }[];
  models: { code: string; major: string; name: string; subs: string[] }[];
  sales_modes: { code: string; name: string }[];
}

export interface Questions {
  questions: {
    version: string;
    scale: { competence: Record<string, string>; competence_guide: string; dna_guide: string };
    dna: DnaItem[];
    competence: CompetenceItem[];
    special_title: string;
    special: SpecialItem[];
  };
  industries: Industries;
  model: {
    version: string;
    areas: Area[];
    dna_axes: DnaAxisMeta[];
    types: Record<string, { name: string; strategy: string }>;
    goals: { default: string; items: Record<string, { name: string; area: string }> };
    sector_groups: Record<string, { name: string }>;
    stage_labels: Record<string, string>;
    notices: Record<string, string>;
  };
}

/** 응답 상태 = 엔진 입력. 비어 있는 값은 null(결측)로 둔다. */
export interface Survey {
  store: {
    name?: string; region?: string; employees?: number | null;
    major?: string; biz_model?: string; sub_industry?: string; sales_mode?: string; goal?: string;
  };
  finance: { monthly_sales?: number | null; material_cost?: number | null; labor_cost?: number | null; rent?: number | null; other_cost?: number | null };
  answers: { dna: Record<string, Likert>; competence: Record<string, Likert>; special: Record<string, Likert> };
  observations: {
    months_operating?: number | null; repeat_rate?: number | null; positive_cashflow_months?: number | null;
    channels?: number | null; staff?: number | null; sales_prev?: number | null;
  };
  benchmark?: { monthly_sales?: number | null; source?: string } | null;
}

export interface AxisResult {
  key: string; name: string; score: number | null; letter: string | null; lean: string | null;
  boundary: boolean | null; answered: number; a?: string; b?: string; a_name?: string; b_name?: string;
}

export interface AreaResult {
  code: string; name: string; detail: string; weight: number;
  common_score: number | null; special_score: number | null; score: number | null;
  answered: number; missing: string[]; special_missing: string[];
}

export interface StrategyItem {
  rank: number; area: string; area_name: string; title: string; action: string; kpi: string;
  priority: number; urgency: number; fit: number; feasibility: number; gated: boolean; rules: string[]; rationale: string;
}

export interface PlanItem { rank: number; area: string; title: string; kpi: string; d30: string; d60: string; d90: string }

export interface DiagnosisResult {
  versions: { model: string; questions: string; industries: string };
  store: { name: string; sector_group: string; sector_name: string; major?: string; biz_model?: string; sub_industry?: string; sales_mode?: string; goal: string; goal_name: string };
  dna: { code: string | null; name: string | null; strategy: string | null; axes: AxisResult[]; boundary_axes: string[]; provisional: boolean; missing: string[]; notice: string };
  competence: {
    areas: AreaResult[]; weights: Record<string, number>; total: number | null;
    grade: { grade: string; name: string } | null; strengths: string[]; weaknesses: string[];
    excluded_areas: string[]; missing_ratio: number; special_areas: string[];
  };
  finance: {
    monthly_sales: number; material_cost: number; labor_cost: number; rent: number; other_cost: number; total_cost: number;
    unanswered_costs: string[]; operating_residual: number; residual_margin_pct: number | null; rent_ratio_pct: number | null;
    material_ratio_pct: number | null; labor_ratio_pct: number | null; cost_ratio_pct: number | null;
  };
  sales_growth_pct: number | null;
  risks: { code: string; level: "high" | "medium"; text: string }[];
  strategies: {
    provisional: boolean; notice: string; items: StrategyItem[]; top: StrategyItem[]; goal: string; goal_area: string;
    action_plan: { draft: boolean; items: PlanItem[] };
  } | null;
  stage: { code: string; label: string; reason: string };
  observations: Record<string, number>;
  benchmark: { source: string; monthly_sales: number; gap_pct: number | null; warning: string } | null;
  confidence: { level: string; evidence_count: number; sector_modules: number; note: string };
  notices: { model: string; residual: string };
}
