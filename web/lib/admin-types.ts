// 관리자 화면(docs/admin.md)의 API 응답 형식. 정본은 api/bizdna_api/admin.py·analytics.py.

export type AdminFilters = {
  industry?: string;
  phase?: "" | "basic" | "full";
  stage?: string;
  dna_type?: string;
  since?: string; // YYYY-MM-DD
  until?: string; // YYYY-MM-DD (그날 포함)
};

export type Count = { key: string; n: number };
export type Quantiles = { p25: number | null; p50: number | null; p75: number | null; mean: number | null };

export type AdminOverview = {
  n: number;
  subjects: number;
  full: number;
  model_versions: Count[];
  dna_types: Count[];
  stages: Count[];
  industries: Count[];
  grades: Count[];
  risks: Count[];
  goals: Count[];
  strategies: Count[];
  total_score: Quantiles;
  axes: {
    axis: string; name: string; a: string; b: string; a_name: string; b_name: string;
    n: number; mean: number | null; a_share: number | null; boundary_share: number | null;
  }[];
  domains: ({ domain: string; name: string } & Quantiles)[];
  funnel: { started: number; basic_completed: number; full_completed: number };
  labels: {
    risks: Record<string, string>;
    goals: Record<string, string>;
    strategies: Record<string, string>;
    types: Record<string, string>;
    stages: Record<string, string>;
  };
  generated_at: string;
};

export type AdminFact = {
  fact_id: string;
  subject_key: string;
  round_no: number;
  phase: "basic" | "full";
  completed_at: string;
  model_version: string;
  industry: string | null;
  founded_year: number | null;
  sales_recent: number | null;
  sales_prev: number | null;
  operating_margin: number | null;
  employees: number | null;
  dna_type: string | null;
  dna_g_dir: number | null;
  dna_i_dir: number | null;
  dna_n_dir: number | null;
  dna_p_dir: number | null;
  stage_code: string | null;
  stage_weighted_index: number | null;
  total_score: number | null;
  grade: string | null;
  goals: string[] | null;
  risk_flags: string[] | null;
  top_strategies: string[] | null;
};

export type AdminFactPage = { total: number; offset: number; limit: number; items: AdminFact[] };

export type AdminFactDetail = AdminFact & {
  customer_type: string[] | null;
  stage_product: number | null; stage_customer: number | null; stage_revenue: number | null;
  stage_cash: number | null; stage_operations: number | null; stage_expansion: number | null;
  stage_gate_adjusted: boolean | null;
  stage_gates: string[] | null;
  competence_missing_ratio: number | null;
  plan: Record<string, string | number | string[]>;
  domain_scores: { domain: string; score: number | null; weight: number; answered: number }[];
  strategy_scores: {
    strategy: string; fit: number | null; urgency: number | null; impact: number | null; feasibility: number | null;
    total: number; rank: number; status: "recommended" | "deferred"; rule_ids: string[];
  }[];
};
