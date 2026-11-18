"use client";

import type { AdminFactDetail, AdminOverview } from "@/lib/admin-types";
import { A_COLOR, B_COLOR } from "./charts";

const AXES = [
  { key: "dna_g_dir", a: "G", b: "S", name: "성장지향" },
  { key: "dna_i_dir", a: "I", b: "E", name: "경쟁전략" },
  { key: "dna_n_dir", a: "N", b: "C", name: "시장전략" },
  { key: "dna_p_dir", a: "P", b: "O", name: "경영방식" },
] as const;

const STAGE_KEYS = [
  ["stage_product", "사업화"], ["stage_customer", "고객검증"], ["stage_revenue", "매출"],
  ["stage_cash", "현금흐름"], ["stage_operations", "조직·운영"], ["stage_expansion", "확장·투자"],
] as const;

const num = (x: number | null | undefined, d = 1) => (x == null ? "-" : x.toFixed(d));

export function FactDetail({ fact, labels, onClose }: {
  fact: AdminFactDetail; labels: AdminOverview["labels"] | null; onClose: () => void;
}) {
  const L = (group: keyof AdminOverview["labels"], k: string) => labels?.[group]?.[k] ?? k;
  return (
    <aside className="fact-detail panel" aria-label="회차 상세">
      <div className="fd-head">
        <div>
          <span className="step-kicker">회차 상세</span>
          <h3>{fact.dna_type ?? "-"} <small>{fact.dna_type ? L("types", fact.dna_type) : ""}</small></h3>
          <p className="muted">
            가명 {fact.subject_key.slice(0, 8)} · {fact.round_no}회차 · {fact.phase === "full" ? "정밀진단" : "기본진단"} ·{" "}
            {new Date(fact.completed_at).toLocaleString("ko-KR")} · 모형 {fact.model_version}
          </p>
        </div>
        <button className="text-btn" onClick={onClose}>닫기</button>
      </div>

      <dl className="fd-grid">
        <div><dt>업종</dt><dd>{fact.industry ?? "-"}</dd></div>
        <div><dt>설립연도</dt><dd>{fact.founded_year ?? "-"}</dd></div>
        <div><dt>최근 매출</dt><dd>{fact.sales_recent != null ? `${fact.sales_recent}억` : "-"}</dd></div>
        <div><dt>전년 매출</dt><dd>{fact.sales_prev != null ? `${fact.sales_prev}억` : "-"}</dd></div>
        <div><dt>영업이익률</dt><dd>{fact.operating_margin != null ? `${fact.operating_margin}%` : "-"}</dd></div>
        <div><dt>인력</dt><dd>{fact.employees != null ? `${fact.employees}명` : "-"}</dd></div>
        <div><dt>주요 고객</dt><dd>{fact.customer_type?.join(", ") || "-"}</dd></div>
        <div><dt>성장단계</dt><dd>{fact.stage_code ?? "-"} {fact.stage_code ? L("stages", fact.stage_code.slice(1)) : ""}
          {fact.stage_gate_adjusted ? <small className="muted"> (Gate 조정: {fact.stage_gates?.join(", ")})</small> : null}</dd></div>
        <div><dt>종합역량</dt><dd>{fact.total_score != null ? `${num(fact.total_score, 2)}점 · ${fact.grade}등급` : "기본진단"}</dd></div>
      </dl>

      <h4>경영자 성향 (방향값)</h4>
      <div className="fd-axes">
        {AXES.map((ax) => {
          const v = fact[ax.key];
          const w = v == null ? 0 : Math.min(Math.abs(v), 100) / 2;
          return (
            <div className="fd-axis" key={ax.key}>
              <span><b style={{ color: B_COLOR }}>{ax.b}</b></span>
              <div className="axis-track small" aria-label={`${ax.name} ${v ?? "응답 없음"}`}>
                <i className="axis-zone" /><i className="axis-mid" />
                {v != null && <i className="axis-bar" style={{ width: `${w}%`, left: v >= 0 ? "50%" : `${50 - w}%`, background: v >= 0 ? A_COLOR : B_COLOR }} />}
              </div>
              <span><b style={{ color: A_COLOR }}>{ax.a}</b></span>
              <span className="fd-axis-v">{v == null ? "-" : `${v > 0 ? "+" : ""}${v.toFixed(2)}`}</span>
            </div>
          );
        })}
      </div>

      <h4>성장단계 6지표 (1~5)</h4>
      <div className="fd-chips">
        {STAGE_KEYS.map(([k, label]) => <span key={k}>{label} <b>{fact[k] ?? "-"}</b></span>)}
      </div>

      {fact.domain_scores.length > 0 && (
        <>
          <h4>8대 역량 점수</h4>
          <div className="fd-domains">
            {fact.domain_scores.map((d) => (
              <div key={d.domain} title={`응답 ${d.answered}/8, 가중치 ${d.weight}`}>
                <span>{d.domain}</span>
                <div className="bar-track"><i style={{ width: `${d.score ?? 0}%` }} /></div>
                <b>{num(d.score)}</b>
              </div>
            ))}
          </div>
          <h4>전략 점수 (순위순)</h4>
          <table className="fd-table">
            <thead><tr><th>순위</th><th>전략</th><th>점수</th><th>상태</th><th>규칙</th></tr></thead>
            <tbody>
              {fact.strategy_scores.map((s) => (
                <tr key={s.strategy} className={s.status === "deferred" ? "deferred" : ""}>
                  <td>{s.rank}</td>
                  <td>{s.strategy} {L("strategies", s.strategy)}</td>
                  <td>{num(s.total, 2)}</td>
                  <td>{s.status === "deferred" ? "보류" : "추천"}</td>
                  <td>{s.rule_ids.join(", ") || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h4>목표·성장장애</h4>
      <div className="fd-chips">
        {(fact.goals ?? []).map((g) => <span key={g}>목표 · {L("goals", g)}</span>)}
        {(fact.risk_flags ?? []).map((r) => <span key={r} className="warn">장애 · {L("risks", r)}</span>)}
        {!fact.goals?.length && !fact.risk_flags?.length && <span className="muted">없음</span>}
      </div>
      <details className="fd-raw">
        <summary>성장계획 문항 원값 (P01~P12)</summary>
        <pre>{JSON.stringify(fact.plan, null, 2)}</pre>
      </details>
    </aside>
  );
}
