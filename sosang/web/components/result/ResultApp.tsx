"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ApiError, downloadReport, runDiagnosis } from "@/lib/api";
import { loadSaved } from "@/lib/storage";
import type { AxisResult, DiagnosisResult, StrategyItem } from "@/lib/types";
import { CompetenceRadar } from "./CompetenceRadar";

// 중소경영 components/result/ResultApp.tsx의 구성을 복사해 소상공인 결과(재무·위험·실행계획)에 맞게 고쳤다.

const won = (v: number) => `${v.toLocaleString("ko-KR")}만원`;
const pct = (v: number | null) => (v === null ? "계산 불가" : `${v.toFixed(1)}%`);

function AxisRow({ axis }: { axis: AxisResult }) {
  const score = axis.score;
  return (
    <div className="axis-row">
      <div className="axis-top">
        <b>{axis.name}</b>
        <span>{score === null ? "판정 불가" : `${score.toFixed(1)}점 · ${axis.lean}`}</span>
      </div>
      <div className="axis-line">
        <span className={axis.letter === axis.b ? "lean" : ""}>{axis.b} {axis.b_name}</span>
        <div className="axis-track" aria-hidden="true">
          <i className="zone" />
          {score !== null && <em style={{ left: `${score}%` }} />}
        </div>
        <span className={axis.letter === axis.a ? "lean" : ""}>{axis.a} {axis.a_name}</span>
      </div>
      {axis.boundary && (
        <p className="axis-note">40~60점 경계 구간입니다. 두 성향이 비슷하게 나타나 유형은 잠정 판정이며, 재진단 때 바뀔 수 있습니다.</p>
      )}
    </div>
  );
}

const FACTORS: [keyof Pick<StrategyItem, "urgency" | "fit" | "feasibility">, string][] = [
  ["urgency", "시급성"], ["fit", "적합도"], ["feasibility", "실행가능성"],
];

function StrategyCard({ s }: { s: StrategyItem }) {
  return (
    <article className="strategy-card">
      <div className="strategy-head">
        <span className="rank">{s.rank}</span>
        <div>
          <h4>{s.title}</h4>
          <small>{s.area_name} · 우선점수 {s.priority.toFixed(2)}</small>
        </div>
      </div>
      <div className="factor-list">
        {FACTORS.map(([k, label]) => (
          <div className="factor" key={k}>
            <span>{label}</span>
            <div className="factor-track"><i style={{ width: `${Math.min(100, s[k])}%` }} /></div>
            <b>{Math.round(s[k])}</b>
          </div>
        ))}
      </div>
      {s.gated && <div className="chips"><span className="chip risk">적자라서 확장성 지출은 뒤로</span></div>}
      <div className="strategy-body">
        <div><small>무엇을 하나요</small><ul><li>{s.action}</li></ul></div>
        <div><small>무엇으로 확인하나요 (성과지표)</small><ul><li>{s.kpi}</li></ul></div>
        <p className="rationale">{s.rationale}</p>
      </div>
    </article>
  );
}

export function ResultApp() {
  // 브라우저에서만 렌더링된다(ResultClient, ssr:false). 이 기기에 저장된 응답으로 결과를 계산한다.
  const [saved] = useState(() => loadSaved());
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const run = useCallback(() => {
    if (!saved?.done) return;
    runDiagnosis(saved.survey)
      .then(setResult)
      .catch((e) => setError(e instanceof ApiError ? e.message : "진단 중 오류가 발생했습니다."));
  }, [saved]);
  useEffect(run, [run]);
  const retry = () => { setError(null); run(); };

  const download = async () => {
    if (!saved || !result) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadReport(saved.survey, result.store.name);
    } catch (e) {
      setDownloadError(e instanceof ApiError ? e.message : "보고서를 만들지 못했습니다.");
    } finally {
      setDownloading(false);
    }
  };

  const wrap = (body: React.ReactNode) => <div className="result-body"><div className="result-wrap">{body}</div></div>;

  if (!saved?.done) {
    return wrap(
      <div className="panel notice-panel">
        <h3>아직 진단 결과가 없습니다</h3>
        <p>자가진단을 마치면 이곳에서 우리 가게 경영유형, 경영역량, 개선전략과 실행계획을 확인할 수 있습니다.</p>
        <Link className="btn btn-primary btn-sm" href="/diagnosis">{saved ? "이어서 진단하기" : "진단 시작하기"}</Link>
      </div>,
    );
  }
  if (error) {
    return wrap(
      <div className="panel notice-panel" role="alert">
        <h3>결과를 계산하지 못했습니다</h3>
        <p>{error}</p>
        <div className="warn-actions">
          <button className="btn btn-dark btn-sm" onClick={retry}>다시 시도</button>
          <Link className="btn btn-line btn-sm" href="/diagnosis">응답 수정하기</Link>
        </div>
      </div>,
    );
  }
  if (!result) return wrap(<div className="panel loading-panel">진단 결과를 계산하는 중입니다…</div>);

  const { dna, competence: comp, finance: fin, strategies: strat } = result;
  const areaName = (c: string) => comp.areas.find((a) => a.code === c)?.name ?? c;
  const top = strat?.top ?? [];

  return (
    <>
      <section className="result-hero">
        <div className="result-wrap">
          <span className="eyebrow">Diagnosis Result</span>
          <div className="result-hero-grid">
            <div>
              <p className="company">{result.store.name} · {result.store.sector_name}{result.store.sub_industry ? ` · ${result.store.sub_industry}` : ""}</p>
              <div className="dna-code" aria-label={`경영유형 ${dna.code ?? "판정 불가"}`}>
                {(dna.code ?? "????").split("").map((c, i) => <span key={i}>{c}</span>)}
              </div>
              <h1>{dna.name ?? "일부 축 판정 불가"}</h1>
              {dna.strategy && <p className="profile">대표 전략방향 <b>{dna.strategy}</b>{dna.provisional && " · 경계 축이 있어 잠정 판정"}</p>}
            </div>
            <div className="hero-stats">
              <div className="stat-box">
                <h4>종합역량</h4>
                <div className="num">{comp.total?.toFixed(1) ?? "-"}<span>점</span></div>
                <small>{comp.grade ? `${comp.grade.grade}등급 · ${comp.grade.name}` : "응답 없음"}</small>
              </div>
              <div className="stat-box">
                <h4>영업잔여액</h4>
                <div className={`num${fin.operating_residual < 0 ? " neg" : ""}`}>{fin.operating_residual.toLocaleString("ko-KR")}<span>만원</span></div>
                <small>월 기준 · 영업이익 아님</small>
              </div>
              <div className="stat-box">
                <h4>1순위 전략</h4>
                <div className="num sm">{top[0]?.title ?? "-"}</div>
                <small>{top[0] ? `우선점수 ${top[0].priority.toFixed(1)}` : ""}</small>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="result-body">
        <div className="result-wrap">
          <section className="panel summary-panel">
            <h3 className="panel-title">한눈에 보기</h3>
            <div className="summary-grid">
              <div><small className="mini-label">잘하고 있는 것</small><p>{comp.strengths.map(areaName).join(", ") || "-"}</p></div>
              <div><small className="mini-label">먼저 챙길 것</small><p>{comp.weaknesses.map(areaName).join(", ") || "-"}</p></div>
              <div><small className="mini-label">위험 신호</small><p>{result.risks.length ? `${result.risks.length}개 (아래 참고)` : "입력값 기준 없음"}</p></div>
              <div><small className="mini-label">내일부터 할 일</small><p>{strat?.action_plan.items[0]?.d30 ?? "-"}</p></div>
            </div>
          </section>

          <div className="result-grid">
            <section className="panel">
              <h3 className="panel-title">경영유형 4축 성향</h3>
              <p className="panel-sub">60점 이상이면 오른쪽, 40점 이하면 왼쪽 성향입니다. 가운데 음영은 경계 구간입니다.</p>
              <div className="axis-list">{dna.axes.map((a) => <AxisRow key={a.key} axis={a} />)}</div>
              <p className="panel-foot">{dna.notice} 유형은 우열이 아니라 운영 성향이며, 재진단 때 바뀔 수 있습니다.</p>
            </section>

            <section className="panel">
              <h3 className="panel-title">매출·비용 구조</h3>
              <p className="panel-sub">월 매출 {won(fin.monthly_sales)} · 비용 합계 {won(fin.total_cost)}</p>
              <div className="domain-list">
                {([["원재료·매입비", fin.material_cost, fin.material_ratio_pct], ["인건비", fin.labor_cost, fin.labor_ratio_pct],
                  ["임대료", fin.rent, fin.rent_ratio_pct], ["기타비용", fin.other_cost, fin.monthly_sales ? (fin.other_cost / fin.monthly_sales) * 100 : null],
                  ["영업잔여액", fin.operating_residual, fin.residual_margin_pct]] as const).map(([label, v, r]) => (
                  <div className="domain" key={label}>
                    <span>{label}</span>
                    <div className="domain-track"><i className={label === "영업잔여액" ? (v < 0 ? "weak" : "strong") : ""} style={{ width: `${Math.max(0, Math.min(100, r ?? 0))}%` }} /></div>
                    <b className="wide-num">{won(v)} · {pct(r)}</b>
                  </div>
                ))}
              </div>
              {result.sales_growth_pct !== null && <p className="panel-sub">전년 같은 달 대비 매출 {result.sales_growth_pct > 0 ? "+" : ""}{result.sales_growth_pct.toFixed(1)}%</p>}
              {result.benchmark && (
                <p className="panel-sub">비교기준 월매출 {won(result.benchmark.monthly_sales)} 대비 {pct(result.benchmark.gap_pct)} <small className="muted">({result.benchmark.warning})</small></p>
              )}
              <small className="mini-label risk-label">위험 신호</small>
              <div className="chips">
                {result.risks.length ? result.risks.map((r) => (
                  <span className={`chip ${r.level === "high" ? "danger" : "risk"}`} key={r.code} title={r.text}>{r.text}</span>
                )) : <span className="muted">입력값 기준으로 해당하는 위험 신호가 없습니다.</span>}
              </div>
              <p className="panel-foot">{result.notices.residual} 위험 기준(임대료 20%, 비용 95% 등)은 시범검증 전 임시 기준입니다.</p>
            </section>
          </div>

          <div className="result-grid">
            <section className="panel">
              <h3 className="panel-title">8대 경영역량</h3>
              <p className="panel-sub">종합 {comp.total?.toFixed(2) ?? "-"}점{comp.grade && ` · ${comp.grade.grade}등급 (${comp.grade.name})`} · {result.store.sector_name} 가중치</p>
              <CompetenceRadar areas={comp.areas} />
            </section>
            <section className="panel">
              <h3 className="panel-title">영역별 점수</h3>
              <div className="domain-list">
                {comp.areas.map((a) => (
                  <div className="domain" key={a.code}>
                    <span>{a.code}. {a.name}</span>
                    <div className="domain-track">
                      <i className={comp.strengths.includes(a.code) ? "strong" : comp.weaknesses.includes(a.code) ? "weak" : ""} style={{ width: `${a.score ?? 0}%` }} />
                    </div>
                    <b>{a.score === null ? "결측" : a.score.toFixed(1)}</b>
                  </div>
                ))}
              </div>
              {comp.special_areas.length > 0 && (
                <p className="panel-foot">업종별 심화진단을 답한 영역({comp.special_areas.map(areaName).join(", ")})은 공통 65% + 심화 35%로 계산했습니다.</p>
              )}
              {comp.missing_ratio > 0 && <p className="panel-foot">미응답 문항 {(comp.missing_ratio * 100).toFixed(0)}%는 0점이 아니라 빈칸으로 보고 제외했습니다.</p>}
            </section>
          </div>

          {strat && (
            <>
              <section className="panel">
                <h3 className="panel-title">먼저 해야 할 개선전략 3가지</h3>
                <p className="panel-sub">
                  점수가 낮은 영역을 그대로 고르지 않고 적자·임대료 부담, 업종, 우선 경영목표({result.store.goal_name})를 함께 봤습니다.
                  우선점수 = 0.45 시급성 + 0.35 적합도 + 0.20 실행가능성
                </p>
                <div className="strategy-list">{top.map((s) => <StrategyCard key={s.area} s={s} />)}</div>
                <p className="panel-foot">{strat.notice}</p>
              </section>

              <section className="panel">
                <h3 className="panel-title">30·60·90일 실행계획</h3>
                <div className="plan-table" role="table" aria-label="30·60·90일 실행계획">
                  <div className="plan-row plan-headrow" role="row">
                    <span role="columnheader">전략</span><span role="columnheader">30일</span><span role="columnheader">60일</span><span role="columnheader">90일</span>
                  </div>
                  {strat.action_plan.items.map((p) => (
                    <div className="plan-row" role="row" key={p.area}>
                      <span role="cell" className="plan-title"><b>{p.rank}</b>{p.title}<small>성과지표: {p.kpi}</small></span>
                      <span role="cell"><em>30일</em>{p.d30}</span>
                      <span role="cell"><em>60일</em>{p.d60}</span>
                      <span role="cell"><em>90일</em>{p.d90}</span>
                    </div>
                  ))}
                </div>
                {strat.action_plan.draft && <p className="panel-foot">실행계획 문구는 초안입니다. 가게 상황에 맞게 조정해서 쓰세요.</p>}
              </section>
            </>
          )}

          <div className="result-grid">
            <section className="panel">
              <h3 className="panel-title">성장단계 · 진단 신뢰도</h3>
              <p className="panel-sub"><b>{result.stage.label}</b>{result.stage.code !== "UNDETERMINED" && ` (${result.stage.code})`} · {result.stage.reason}</p>
              <p className="panel-sub">신뢰도 <b>{result.confidence.level}</b> · 실적 입력 {result.confidence.evidence_count}개 · 업종 심화 {result.confidence.sector_modules}/3영역</p>
              <p className="panel-foot">{result.confidence.note}</p>
            </section>
            <section className="panel report-panel">
              <div>
                <h3 className="panel-title">진단 보고서</h3>
                <p className="panel-sub">점포 현황, 경영유형, 8대 역량, 매출·비용과 위험, 개선전략 3가지, 30·60·90일 실행계획을 담은 기본형 PDF(6쪽)입니다.</p>
                {downloadError && <p className="error-text" role="alert">{downloadError}</p>}
              </div>
              <button className="btn btn-dark btn-sm" disabled={downloading || !strat} onClick={download}>
                {downloading ? "만드는 중…" : "기본형 PDF 받기"}
              </button>
            </section>
          </div>

          <div className="result-foot">
            <Link className="btn btn-line btn-sm" href="/diagnosis">응답 수정하기</Link>
            <p>
              {result.notices.model} 모형 {result.versions.model} · 문항 {result.versions.questions} · 업종분류 {result.versions.industries}.
              결과는 이 기기(브라우저)에만 저장됩니다.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
