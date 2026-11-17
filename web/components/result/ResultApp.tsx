"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, downloadReport, getDiagnosis, runDiagnosis } from "@/lib/api";
import { FIRST_FULL_STEP, loadSaved, save, type SavedSurvey } from "@/lib/storage";
import type { Axis, DiagnosisResult, Strategy } from "@/lib/types";
import { CompetenceRadar } from "./CompetenceRadar";

const STAGES = ["사업모델 탐색기", "시장검증기", "사업화 안정기", "성장확장기", "규모화·재도약기"];
const INDICATORS: Record<string, string> = {
  product: "제품·서비스 사업화", customer: "고객검증·반복구매", revenue: "매출 발생·성장",
  cash: "수익모델·현금흐름", operations: "조직·운영체계", expansion: "시장확장·투자실행",
};
const AXIS_SIDES: Record<string, [string, string]> = {
  growth: ["S 안정내실", "G 성장확장"], competition: ["E 효율경쟁", "I 혁신차별"],
  market: ["C 기존시장집중", "N 시장개척"], management: ["O 창업자주도", "P 조직체계"],
};
const FACTORS: [keyof Strategy["factors"], string][] = [["fit", "적합성"], ["urgency", "시급성"], ["impact", "기대효과"], ["feasibility", "실행가능성"]];

function AxisRow({ name, axis }: { name: string; axis: Axis }) {
  const [left, right] = AXIS_SIDES[axis.key];
  const score = axis.score;
  return (
    <div className="axis-row">
      <div className="axis-top">
        <b>{name}</b>
        <span>{score === null ? "판정 불가" : `${score.toFixed(1)}점 · ${axis.tendency}`}</span>
      </div>
      <div className="axis-line">
        <span className={axis.letter === left[0] ? "lean" : ""}>{left}</span>
        <div className="axis-track" aria-hidden="true">
          <i className="zone" />
          {score !== null && <em style={{ left: `${score}%` }} />}
        </div>
        <span className={axis.letter === right[0] ? "lean" : ""}>{right}</span>
      </div>
      {(axis.boundary || axis.low_reliability) && (
        <p className="axis-note">
          {axis.boundary && "40~60점 경계 구간입니다. 두 성향이 비슷하게 나타나 재진단 때 바뀔 수 있습니다. "}
          {axis.low_reliability && `응답 ${axis.answered}/6문항으로 판정해 신뢰도가 낮습니다.`}
        </p>
      )}
    </div>
  );
}

function StrategyCard({ s, rank }: { s: Strategy; rank: number }) {
  return (
    <article className="strategy-card">
      <div className="strategy-head">
        <span className="rank">{rank}</span>
        <div>
          <h4>{s.name}</h4>
          <small>{s.code} · 추천점수 {s.score.toFixed(2)}</small>
        </div>
      </div>
      <div className="factor-list">
        {FACTORS.map(([k, label]) => (
          <div className="factor" key={k}>
            <span>{label}</span>
            <div className="factor-track"><i style={{ width: `${s.factors[k]}%` }} /></div>
            <b>{Math.round(s.factors[k])}</b>
          </div>
        ))}
      </div>
      {(s.reasons.length > 0 || s.matched_goals.length > 0) && (
        <div className="chips">
          {s.reasons.map((r, i) => <span className="chip" key={r}>{s.applied_rules[i]} · {r}</span>)}
          {s.matched_goals.length > 0 && <span className="chip soft">목표 일치 {s.matched_goals.length}개</span>}
        </div>
      )}
      <div className="strategy-body">
        <div><small>실행과제</small><ul>{s.actions.map((a) => <li key={a}>{a}</li>)}</ul></div>
        <div><small>핵심 성과지표</small><ul>{s.kpis.map((a) => <li key={a}>{a}</li>)}</ul></div>
      </div>
    </article>
  );
}

export function ResultApp() {
  const router = useRouter();
  // 브라우저에서만 렌더링된다(ResultClient, ssr:false).
  // ?id=… 이면 내 계정에 최종저장된 회차(저장 당시 결과)를, 아니면 이 브라우저의 응답으로 계산한 결과를 보여준다.
  const [serverId] = useState(() => new URLSearchParams(window.location.search).get("id"));
  const [saved, setSaved] = useState<SavedSurvey | null>(() => (serverId ? null : loadSaved()));
  const [savedInfo, setSavedInfo] = useState<{ completedAt: string | null; modelVersion: string | null } | null>(null);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // 서버 회차는 저장 당시 결과를 그대로 보여준다(엔진을 다시 돌리지 않음 → 당시 모형 버전으로 재현).
  const loadServer = useCallback(() => {
    if (!serverId) return;
    getDiagnosis(serverId).then((rec) => {
        if (!rec.result) throw new ApiError("아직 최종저장되지 않은 진단입니다. 마이페이지에서 이어서 진단하세요.");
        const p = rec.progress ?? {};
        setSaved({
          survey: rec.survey, step: p.step ?? 0, maxStep: p.maxStep ?? 0, basicDone: true, phase: rec.phase,
          savedAt: rec.updated_at, diagnosisId: rec.id,
        });
        setSavedInfo({ completedAt: rec.completed_at, modelVersion: rec.model_version });
        setResult(rec.result);
      }).catch((e) => setError(e instanceof ApiError ? e.message : "저장된 진단을 불러오지 못했습니다."));
  }, [serverId]);

  const runLocal = useCallback(() => {
    if (serverId || !saved?.basicDone) return;
    runDiagnosis(saved.survey, saved.phase)
      .then(setResult)
      .catch((e) => setError(e instanceof ApiError ? e.message : "진단 중 오류가 발생했습니다."));
  }, [saved, serverId]);
  const retry = () => { setError(null); if (serverId) loadServer(); else runLocal(); };

  useEffect(loadServer, [loadServer]);
  useEffect(runLocal, [runLocal]);

  const continueFull = () => {
    if (!saved) return;
    const step = Math.max(saved.step, FIRST_FULL_STEP);
    const maxStep = Math.max(saved.maxStep, FIRST_FULL_STEP);
    if (saved.diagnosisId) {
      // 회원 회차: 서버 응답을 기준으로 정밀진단을 이어 한다.
      router.push(`/diagnosis?id=${saved.diagnosisId}&step=${step}`);
      return;
    }
    save({ ...saved, step, maxStep });
    router.push("/diagnosis");
  };

  const download = async (mode: "basic" | "advanced") => {
    if (!saved || !result) return;
    setDownloading(mode);
    setDownloadError(null);
    try {
      await downloadReport(saved.survey, mode, String(result.company.name ?? ""));
    } catch (e) {
      setDownloadError(e instanceof ApiError ? e.message : "보고서를 만들지 못했습니다.");
    } finally {
      setDownloading(null);
    }
  };

  if (serverId && !saved && !error) {
    return <div className="result-body"><div className="result-wrap"><div className="panel loading-panel">저장된 진단을 불러오는 중입니다…</div></div></div>;
  }
  if (!error && (!saved || !saved.basicDone)) {
    return (
      <div className="result-body"><div className="result-wrap">
        <div className="panel notice-panel">
          <h3>아직 진단 결과가 없습니다</h3>
          <p>기본진단을 마치면 이곳에서 기업 DNA 유형과 성장단계를 확인할 수 있습니다.</p>
          <Link className="btn btn-primary btn-sm" href="/diagnosis">진단 시작하기</Link>
        </div>
      </div></div>
    );
  }
  if (error) {
    return (
      <div className="result-body"><div className="result-wrap">
        <div className="panel notice-panel" role="alert">
          <h3>결과를 계산하지 못했습니다</h3>
          <p>{error}</p>
          <div className="warn-actions">
            <button className="btn btn-dark btn-sm" onClick={retry}>다시 시도</button>
            <Link className="btn btn-line btn-sm" href={serverId ? "/mypage" : "/diagnosis"}>{serverId ? "마이페이지로" : "응답 수정하기"}</Link>
          </div>
        </div>
      </div></div>
    );
  }
  if (!result) return <div className="result-body"><div className="result-wrap"><div className="panel loading-panel">진단 결과를 계산하는 중입니다…</div></div></div>;

  const { dna, stage, competence } = result;
  const full = result.mode === "full" && competence;
  const top3 = result.top_recommended?.slice(0, 3) ?? [];
  const deferred = result.strategies?.filter((s) => s.status === "deferred") ?? [];
  const companyName = String(result.company.name ?? "우리 기업");

  return (
    <>
      <section className="result-hero">
        <div className="result-wrap">
          <span className="eyebrow">{full ? "Full Diagnosis Result" : "Basic Diagnosis Result"}</span>
          <div className="result-hero-grid">
            <div>
              <p className="company">{companyName}</p>
              <div className="dna-code" aria-label={`DNA 유형 ${dna.type}`}>
                {dna.type.split("").map((c, i) => <span key={i}>{c}</span>)}
              </div>
              <h1>{dna.name ?? "일부 축 판정 불가"}</h1>
              {dna.profile && <p className="profile">{dna.profile.traits} · 기본 성장전략 <b>{dna.profile.strategy}</b></p>}
            </div>
            <div className="hero-stats">
              <div className="stat-box"><h4>성장단계</h4><div className="num">{stage?.code ?? "-"}</div><small>{stage?.name ?? "판정 불가"}</small></div>
              {full ? (
                <>
                  <div className="stat-box"><h4>종합역량</h4><div className="num">{competence.total.toFixed(2)}<span>점</span></div><small>{competence.grade.grade}등급 · {competence.grade.name}</small></div>
                  <div className="stat-box"><h4>우선 전략</h4><div className="num sm">{top3[0]?.name ?? "-"}</div><small>{top3[0] ? `${top3[0].code} · ${top3[0].score.toFixed(1)}점` : ""}</small></div>
                </>
              ) : (
                <div className="stat-box"><h4>성장장애</h4><div className="num">{result.risks.length}<span>개</span></div><small>{result.risks.join(" · ") || "선택 없음"}</small></div>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="result-body">
        <div className="result-wrap">
          {!full && (
            <div className="panel cta-panel">
              <div>
                <h3>정밀진단을 이어서 진행하세요</h3>
                <p>8대 경영역량 64문항과 성장계획에 답하면 역량 점수, 우선 성장전략 3개, 실행과제, PDF 보고서를 받을 수 있습니다.</p>
              </div>
              <button className="btn btn-primary" onClick={continueFull}>정밀진단 계속하기 <span aria-hidden="true">→</span></button>
            </div>
          )}

          <div className="result-grid">
            <section className="panel">
              <h3 className="panel-title">DNA 4축 성향</h3>
              <p className="panel-sub">60점 이상이면 오른쪽, 40점 이하면 왼쪽 성향입니다. 가운데 음영은 경계 구간입니다.</p>
              <div className="axis-list">
                {Object.entries(dna.axes).map(([name, axis]) => <AxisRow key={name} name={name} axis={axis} />)}
              </div>
              <p className="panel-foot">유형은 우열이 아니라 전략 성향입니다. 재진단 때 바뀔 수 있습니다.</p>
            </section>

            <section className="panel">
              <h3 className="panel-title">성장단계</h3>
              {stage?.code ? (
                <>
                  <ol className="stage-track">
                    {STAGES.map((n, i) => (
                      <li key={n} className={i + 1 === stage.level ? "on" : i + 1 < (stage.level ?? 0) ? "past" : ""}>
                        <b>S{i + 1}</b><span>{n}</span>
                      </li>
                    ))}
                  </ol>
                  <p className="panel-sub">핵심 과제: <b>{stage.task}</b> · 가중지수 {stage.weighted_index?.toFixed(2)} / 5</p>
                  <div className="indicator-list">
                    {Object.entries(stage.inputs ?? {}).map(([k, v]) => (
                      <div className="indicator" key={k}>
                        <span>{INDICATORS[k]}</span>
                        <div className="dots" aria-label={`${v}단계`}>{[1, 2, 3, 4, 5].map((d) => <i key={d} className={d <= v ? "on" : ""} />)}</div>
                      </div>
                    ))}
                  </div>
                  {stage.gate_adjusted && (
                    <div className="gate-note">
                      가중지수로는 {stage.provisional}이지만 필수 통과조건을 충족하지 못해 {stage.code}로 판정했습니다.
                      <ul>{stage.gates_applied?.map((g) => <li key={g.id}>{g.id}: {g.reason}</li>)}</ul>
                    </div>
                  )}
                </>
              ) : (
                <p className="panel-sub">성장단계 문항에 모두 답하면 판정합니다.</p>
              )}
            </section>
          </div>

          <section className="panel">
            <h3 className="panel-title">경영목표와 성장장애</h3>
            <div className="two-col">
              <div><small className="mini-label">3년 경영목표</small><div className="chips">{result.goals.map((g) => <span className="chip" key={g.code}>{g.name}</span>)}</div></div>
              <div>
                <small className="mini-label">전략추천에 반영되는 성장장애</small>
                <div className="chips">
                  {result.risks.length ? result.risks.map((r) => <span className="chip risk" key={r}>{r}</span>) : <span className="muted">선택한 위험요인이 없습니다.</span>}
                </div>
              </div>
            </div>
          </section>

          {full && (
            <>
              <div className="result-grid">
                <section className="panel">
                  <h3 className="panel-title">8대 경영역량</h3>
                  <p className="panel-sub">종합 {competence.total.toFixed(2)}점 · {competence.grade.grade}등급 ({competence.grade.meaning})</p>
                  <CompetenceRadar domains={competence.domains} />
                </section>
                <section className="panel">
                  <h3 className="panel-title">영역별 점수</h3>
                  <div className="domain-list">
                    {Object.entries(competence.domains).map(([k, v]) => (
                      <div className="domain" key={k}>
                        <span>{k}. {competence.names[k]}</span>
                        <div className="domain-track"><i className={v !== null && v >= 70 ? "strong" : v !== null && v < 55 ? "weak" : ""} style={{ width: `${v ?? 0}%` }} /></div>
                        <b>{v === null ? "결측" : v.toFixed(1)}</b>
                      </div>
                    ))}
                  </div>
                  {competence.missing.length > 0 && <p className="panel-foot">미응답 {competence.missing.length}문항은 0점이 아니라 결측으로 제외했습니다.</p>}
                </section>
              </div>

              <section className="panel">
                <h3 className="panel-title">우선 성장전략</h3>
                <p className="panel-sub">점수가 낮은 영역을 고르는 방식이 아니라, 목표 달성을 가장 막는 제약을 기준으로 골랐습니다. R = 0.30 적합성 + 0.30 시급성 + 0.25 기대효과 + 0.15 실행가능성</p>
                <div className="strategy-list">{top3.map((s, i) => <StrategyCard key={s.code} s={s} rank={i + 1} />)}</div>
                {deferred.length > 0 && (
                  <div className="deferred">
                    <small className="mini-label">선행조건 미충족으로 보류한 전략</small>
                    <ul>{deferred.map((s) => <li key={s.code}><b>{s.name}</b> ({s.code}) · {s.reasons.join(" / ")}</li>)}</ul>
                  </div>
                )}
              </section>

              <section className="panel report-panel">
                <div>
                  <h3 className="panel-title">진단 보고서</h3>
                  <p className="panel-sub">기본형은 핵심 진단과 전략을, 정밀형은 전략 선정근거와 90일 실행계획, 로드맵까지 담습니다.</p>
                  {downloadError && <p className="error-text" role="alert">{downloadError}</p>}
                </div>
                <div className="warn-actions">
                  <button className="btn btn-dark btn-sm" disabled={!!downloading} onClick={() => download("basic")}>{downloading === "basic" ? "만드는 중…" : "기본형 PDF 받기"}</button>
                  <button className="btn btn-line btn-sm" disabled={!!downloading} onClick={() => download("advanced")}>{downloading === "advanced" ? "만드는 중…" : "정밀형 PDF 받기"}</button>
                </div>
              </section>
            </>
          )}

          <div className="result-foot">
            <Link className="btn btn-line btn-sm" href={serverId ? "/mypage" : "/diagnosis"}>{serverId ? "마이페이지로" : "응답 수정하기"}</Link>
            <p>
              {result.limitations.join(" · ")}. 모형 {result.model_version} · 문항 {result.questions_version}.{" "}
              {savedInfo
                ? `내 계정에 저장된 결과입니다${savedInfo.completedAt ? ` (${new Date(savedInfo.completedAt).toLocaleString("ko-KR")} 최종저장)` : ""}.`
                : "결과는 이 브라우저에만 저장됩니다."}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
