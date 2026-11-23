"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, fetchQuestions } from "@/lib/api";
import { SAMPLE_SURVEY } from "@/lib/sample";
import { clearSaved, emptySurvey, save, type SavedSurvey } from "@/lib/storage";
import type { Likert, Questions, Survey } from "@/lib/types";
import { ChoiceField, DnaQuestion, IndustryPicker, LikertQuestion, NumberField, TextField } from "./fields";

// 중소경영 components/survey/SurveyApp.tsx를 복사해 고쳤다. 지금은 게스트(브라우저 저장)만 있다.
// 단계: 업종·점포 → 매출·비용 → 경영유형 4축 → 경영역량 4쪽(2영역씩) → 업종별 심화(선택) → 실적·참고자료(선택)

type Step =
  | { id: string; kind: "store" | "finance" | "special" | "extra"; title: string; caption: string; optional?: boolean }
  | { id: string; kind: "dna"; title: string; caption: string; axis: string }
  | { id: string; kind: "competence"; title: string; caption: string; areas: string[] };

const COMP_PAGES = [["A", "B"], ["C", "D"], ["E", "F"], ["G", "H"]];
const isEmpty = (v: unknown) => v === undefined || v === null || v === "" || (typeof v === "number" && !Number.isFinite(v));

function sectorOf(q: Questions, s: Survey): string {
  return q.industries.majors.find((m) => m.code === s.store.major)?.sector_group ?? "other";
}

function buildSteps(q: Questions, sector: string): Step[] {
  const areaName = (c: string) => q.model.areas.find((a) => a.code === c)?.name ?? c;
  const hasSpecial = q.questions.special.some((i) => i.sector === sector);
  return [
    { id: "store", kind: "store", title: "업종·점포 정보", caption: "업종과 영업방식, 이번 진단에서 가장 먼저 이루고 싶은 목표를 고릅니다." },
    { id: "finance", kind: "finance", title: "매출·비용", caption: "최근 몇 달의 평균을 한 달 기준으로 적습니다. 정확하지 않아도 괜찮습니다." },
    ...q.model.dna_axes.map((a): Step => ({
      id: `dna-${a.key}`, kind: "dna", axis: a.key, title: `경영유형 · ${a.name}`,
      caption: `${a.b_name}과 ${a.a_name} 가운데 우리 가게에 더 가까운 쪽을 고릅니다.`,
    })),
    ...COMP_PAGES.map((areas): Step => ({
      id: `comp-${areas.join("")}`, kind: "competence", areas,
      title: `경영역량 · ${areas.map(areaName).join(", ")}`, caption: q.questions.scale.competence_guide,
    })),
    ...(hasSpecial ? [{ id: "special", kind: "special", optional: true, title: q.questions.special_title,
      caption: "우리 업종에만 해당하는 문항입니다. 답하면 상품·고객관리·점포운영 점수에 35%만큼 반영됩니다." } as Step] : []),
    { id: "extra", kind: "extra", optional: true, title: "실적·참고자료 (선택)",
      caption: "운영기간·재방문율·흑자월 수를 모두 입력하면 성장단계를 잠정 판정합니다. 비워 두어도 결과는 나옵니다." },
  ];
}

/** 단계별 [필수 미응답, 선택 미응답] */
function missingFor(step: Step, q: Questions, s: Survey): { required: string[]; optional: string[] } {
  switch (step.kind) {
    case "store":
      return { required: (["major", "biz_model", "sales_mode", "goal"] as const).filter((k) => isEmpty(s.store[k])), optional: [] };
    case "finance": {
      const required = isEmpty(s.finance.monthly_sales) ? ["monthly_sales"] : [];
      const optional = (["material_cost", "labor_cost", "rent", "other_cost"] as const).filter((k) => isEmpty(s.finance[k]));
      return { required, optional };
    }
    case "dna":
      return { required: [], optional: q.questions.dna.filter((i) => i.axis === step.axis && isEmpty(s.answers.dna[i.code])).map((i) => i.code) };
    case "competence":
      return { required: [], optional: q.questions.competence.filter((i) => step.areas.includes(i.area) && isEmpty(s.answers.competence[i.code])).map((i) => i.code) };
    case "special":
    case "extra":
      return { required: [], optional: [] };
  }
}

function countFor(step: Step, q: Questions, s: Survey, sector: string): [answered: number, total: number] {
  const n = (codes: string[], src: Record<string, unknown>) => [codes.filter((c) => !isEmpty(src[c])).length, codes.length] as [number, number];
  switch (step.kind) {
    case "store": return n(["major", "biz_model", "sales_mode", "goal"], s.store);
    case "finance": return n(["monthly_sales", "material_cost", "labor_cost", "rent", "other_cost"], s.finance);
    case "dna": return n(q.questions.dna.filter((i) => i.axis === step.axis).map((i) => i.code), s.answers.dna);
    case "competence": return n(q.questions.competence.filter((i) => step.areas.includes(i.area)).map((i) => i.code), s.answers.competence);
    case "special": return n(q.questions.special.filter((i) => i.sector === sector).map((i) => i.code), s.answers.special);
    case "extra": return n(["months_operating", "repeat_rate", "positive_cashflow_months"], s.observations);
  }
}

export function SurveyApp({ initial }: { initial: SavedSurvey | null }) {
  const router = useRouter();
  const [q, setQ] = useState<Questions | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [survey, setSurvey] = useState<Survey>(() => initial?.survey ?? emptySurvey());
  const [step, setStep] = useState(initial?.step ?? 0);
  const [maxStep, setMaxStep] = useState(initial?.maxStep ?? 0);
  const [done, setDone] = useState(initial?.done ?? false);
  const [savedAt, setSavedAt] = useState<string | null>(initial?.savedAt ?? null);
  const [toast, setToast] = useState<string | null>(null);
  const [warn, setWarn] = useState<{ required: string[]; optional: string[] } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  const fetchAll = useCallback(() => {
    fetchQuestions().then(setQ).catch((e) => setLoadError(e instanceof ApiError ? e.message : "문항을 불러오지 못했습니다."));
  }, []);
  useEffect(fetchAll, [fetchAll]);
  const retry = () => { setLoadError(null); fetchAll(); };

  const sector = q ? sectorOf(q, survey) : "other";
  const steps = useMemo(() => (q ? buildSteps(q, sector) : []), [q, sector]);
  const safeStep = Math.min(step, Math.max(steps.length - 1, 0));
  const current = steps[safeStep];

  const persist = (next: Partial<{ survey: Survey; step: number; maxStep: number; done: boolean }>) => {
    const at = save({ survey: next.survey ?? survey, step: next.step ?? safeStep, maxStep: next.maxStep ?? maxStep, done: next.done ?? done });
    if (at) setSavedAt(at);
    return at;
  };

  const update = (fn: (s: Survey) => Survey) => {
    setSurvey((prev) => {
      const next = fn(prev);
      save({ survey: next, step: safeStep, maxStep, done });
      return next;
    });
    setSavedAt(new Date().toISOString());
    setWarn(null);
  };
  const setStore = (patch: Partial<Survey["store"]>) => update((s) => ({ ...s, store: { ...s.store, ...patch } }));
  const setFinance = (k: keyof Survey["finance"], v: number | null) => update((s) => ({ ...s, finance: { ...s.finance, [k]: v } }));
  const setObs = (k: keyof Survey["observations"], v: number | null) => update((s) => ({ ...s, observations: { ...s.observations, [k]: v } }));
  const setAnswer = (section: "dna" | "competence" | "special", code: string, v: Likert) =>
    update((s) => ({ ...s, answers: { ...s.answers, [section]: { ...s.answers[section], [code]: v } } }));
  const setBenchmark = (v: number | null) =>
    update((s) => ({ ...s, benchmark: v === null ? null : { monthly_sales: v, source: "사용자 입력 비교기준" } }));

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };
  const scrollTop = () => window.scrollTo({ top: document.getElementById("survey-top")?.offsetTop ?? 0, behavior: "smooth" });

  const goTo = (i: number) => {
    setStep(i);
    setWarn(null);
    persist({ step: i });
    scrollTop();
  };

  const next = (force = false) => {
    if (!q || !current) return;
    const m = missingFor(current, q, survey);
    if (m.required.length || (m.optional.length && !force)) {
      setWarn(m);
      document.getElementById(`q-${m.required[0] ?? m.optional[0]}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (safeStep === steps.length - 1) {
      setDone(true);
      persist({ done: true });
      router.push("/diagnosis/result");
      return;
    }
    const n = safeStep + 1;
    const mx = Math.max(maxStep, n);
    setMaxStep(mx);
    setStep(n);
    setWarn(null);
    persist({ step: n, maxStep: mx });
    scrollTop();
  };

  const saveNow = () => {
    const at = persist({});
    showToast(at ? "저장했습니다. 이 기기에서 이어서 진단할 수 있습니다." : "이 브라우저에서는 저장할 수 없습니다.");
  };

  const fillSample = () => {
    const mx = steps.length - 1;
    setSurvey(SAMPLE_SURVEY);
    setMaxStep(mx);
    save({ survey: SAMPLE_SURVEY, step: safeStep, maxStep: mx, done });
    setSavedAt(new Date().toISOString());
    showToast("가상 점포(동네카페) 예시 응답으로 채웠습니다.");
  };

  const reset = () => {
    clearSaved();
    setSurvey(emptySurvey());
    setStep(0); setMaxStep(0); setDone(false); setSavedAt(null); setConfirmReset(false); setWarn(null);
    showToast("응답을 모두 지웠습니다.");
  };

  if (loadError) {
    return (
      <div className="survey-body"><div className="survey-wrap single">
        <div className="panel notice-panel" role="alert">
          <h3>문항을 불러오지 못했습니다</h3>
          <p>{loadError}</p>
          <p className="muted">개발 환경에서는 sosang/api 폴더에서 <code>uvicorn sosang_api.main:app --port 8001</code>을 실행해야 합니다.</p>
          <button className="btn btn-dark btn-sm" onClick={retry}>다시 시도</button>
        </div>
      </div></div>
    );
  }
  if (!q || !current) {
    return <div className="survey-body"><div className="survey-wrap single"><div className="panel loading-panel">문항을 불러오는 중입니다…</div></div></div>;
  }

  const [answered, total] = steps.filter((s) => !("optional" in s && s.optional))
    .reduce(([a, t], s) => { const [x, y] = countFor(s, q, survey, sector); return [a + x, t + y]; }, [0, 0]);
  const pct = total ? Math.round((answered / total) * 100) : 0;
  const missingSet = new Set(warn ? [...warn.required, ...warn.optional] : []);
  const isLast = safeStep === steps.length - 1;
  const hhmm = (iso: string) => new Date(iso).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
  const goals = Object.entries(q.model.goals.items).map(([value, g]) => ({ value, label: g.name }));
  const specialItems = q.questions.special.filter((i) => i.sector === sector);
  const areaName = (c: string) => q.model.areas.find((a) => a.code === c)?.name ?? c;
  const sectorName = q.model.sector_groups[sector]?.name ?? "기타";

  return (
    <div className="survey-body" id="survey-top">
      <div className="survey-wrap">
        <aside className="survey-side" aria-label="진단 단계">
          <div className="side-inner">
            <div className="step-group">
              <div className="side-title">자가진단</div>
              <ol>
                {steps.map((s, i) => {
                  const [x, y] = countFor(s, q, survey, sector);
                  return (
                    <li key={s.id}>
                      <button
                        className={`step-link${i === safeStep ? " active" : ""}${x === y ? " done" : ""}`}
                        disabled={i > maxStep}
                        onClick={() => goTo(i)}
                        aria-current={i === safeStep ? "step" : undefined}
                      >
                        <span className="indicator" />
                        <span className="step-name">{s.title}</span>
                        <span className="step-count">{x}/{y}</span>
                      </button>
                    </li>
                  );
                })}
              </ol>
            </div>
            <div className="side-tools">
              <button className="text-btn" onClick={fillSample}>예시 점포로 채우기</button>
              {confirmReset ? (
                <span className="inline-confirm">
                  모두 지울까요?
                  <button className="text-btn danger" onClick={reset}>지우기</button>
                  <button className="text-btn" onClick={() => setConfirmReset(false)}>취소</button>
                </span>
              ) : (
                <button className="text-btn" onClick={() => setConfirmReset(true)}>처음부터 다시</button>
              )}
            </div>
          </div>
        </aside>

        <div className="survey-main">
          <div className="step-head">
            <span className="step-kicker">{safeStep + 1}/{steps.length}단계</span>
            <h2>{current.title}</h2>
            <p>{current.caption}</p>
          </div>

          <div className="panel">
            {current.kind === "store" && (
              <div className="company-grid">
                <IndustryPicker industries={q.industries} major={survey.store.major} model={survey.store.biz_model}
                  sub={survey.store.sub_industry} missing={warn?.required ?? []} onChange={setStore} />
                <ChoiceField id="sales_mode" label="주된 영업방식" required missing={missingSet.has("sales_mode")}
                  options={q.industries.sales_modes.map((m) => ({ value: m.code, label: m.name }))}
                  value={survey.store.sales_mode} onChange={(v) => setStore({ sales_mode: v })} />
                <ChoiceField id="goal" label="이번 진단의 우선 경영목표" required missing={missingSet.has("goal")}
                  help="하나만 고릅니다. 개선전략의 우선순위에 반영됩니다."
                  options={goals} value={survey.store.goal} onChange={(v) => setStore({ goal: v })} />
                <TextField id="name" label="점포 이름 (선택)" placeholder="보고서에 표시됩니다" value={survey.store.name}
                  onChange={(v) => setStore({ name: v })} />
                <TextField id="region" label="지역 (선택)" placeholder="예: 서울 마포구" value={survey.store.region}
                  onChange={(v) => setStore({ region: v })} />
                <NumberField id="employees" label="종사자 수 (선택)" unit="명, 점주 포함" value={survey.store.employees}
                  onChange={(v) => setStore({ employees: v })} />
              </div>
            )}

            {current.kind === "finance" && (
              <>
                <p className="panel-prompt">금액은 <b>만원</b> 단위, <b>한 달 평균</b>입니다. 모르는 항목은 비워 두면 0으로 계산합니다.</p>
                <div className="company-grid">
                  <NumberField id="monthly_sales" label="월평균 매출" unit="만원" required missing={missingSet.has("monthly_sales")}
                    value={survey.finance.monthly_sales} onChange={(v) => setFinance("monthly_sales", v)} />
                  <NumberField id="material_cost" label="원재료·상품 매입비" unit="만원" missing={missingSet.has("material_cost")}
                    value={survey.finance.material_cost} onChange={(v) => setFinance("material_cost", v)} />
                  <NumberField id="labor_cost" label="인건비" unit="만원" help="직원 급여·4대보험 등(점주 본인 몫 제외)"
                    missing={missingSet.has("labor_cost")} value={survey.finance.labor_cost} onChange={(v) => setFinance("labor_cost", v)} />
                  <NumberField id="rent" label="임대료" unit="만원" help="월세·관리비" missing={missingSet.has("rent")}
                    value={survey.finance.rent} onChange={(v) => setFinance("rent", v)} />
                  <NumberField id="other_cost" label="기타비용" unit="만원" help="공과금·카드수수료·배달수수료·광고비 등"
                    missing={missingSet.has("other_cost")} value={survey.finance.other_cost} onChange={(v) => setFinance("other_cost", v)} />
                </div>
                <FinancePreview survey={survey} />
              </>
            )}

            {current.kind === "dna" && (
              <>
                <p className="panel-prompt">{q.questions.scale.dna_guide}</p>
                <div className="q-list">
                  {q.questions.dna.filter((i) => i.axis === current.axis).map((i) => (
                    <DnaQuestion key={i.code} item={i} value={survey.answers.dna[i.code]}
                      missing={missingSet.has(i.code)} onChange={(v) => setAnswer("dna", i.code, v)} />
                  ))}
                </div>
              </>
            )}

            {current.kind === "competence" && current.areas.map((area) => (
              <div className="area-block" key={area}>
                <h3 className="area-title"><span>{area}</span>{areaName(area)}</h3>
                <div className="q-list">
                  {q.questions.competence.filter((i) => i.area === area).map((i) => (
                    <LikertQuestion key={i.code} code={i.code} text={i.text} value={survey.answers.competence[i.code]}
                      missing={missingSet.has(i.code)} onChange={(v) => setAnswer("competence", i.code, v)} />
                  ))}
                </div>
              </div>
            ))}

            {current.kind === "special" && (
              <>
                <p className="panel-prompt">{sectorName} 심화진단입니다. 건너뛰어도 되고, 일부만 답해도 됩니다.</p>
                {["B", "C", "F"].map((area) => (
                  <div className="area-block" key={area}>
                    <h3 className="area-title"><span>{area}</span>{areaName(area)}</h3>
                    <div className="q-list">
                      {specialItems.filter((i) => i.area === area).map((i) => (
                        <LikertQuestion key={i.code} code={i.code} text={i.text} value={survey.answers.special[i.code]}
                          missing={false} onChange={(v) => setAnswer("special", i.code, v)} />
                      ))}
                    </div>
                  </div>
                ))}
              </>
            )}

            {current.kind === "extra" && (
              <>
                <div className="company-grid">
                  <NumberField id="months_operating" label="운영기간" unit="개월" value={survey.observations.months_operating}
                    onChange={(v) => setObs("months_operating", v)} />
                  <NumberField id="repeat_rate" label="재방문 고객 비율" unit="%" max={100} help="손님 10명 중 다시 온 손님이 3명이면 30"
                    value={survey.observations.repeat_rate} onChange={(v) => setObs("repeat_rate", v)} />
                  <NumberField id="positive_cashflow_months" label="최근 12개월 중 흑자인 달" unit="개월, 0~12" max={12}
                    value={survey.observations.positive_cashflow_months} onChange={(v) => setObs("positive_cashflow_months", v)} />
                  <NumberField id="sales_prev" label="전년 같은 달 매출" unit="만원" help="매출 증감률 계산에 씁니다"
                    value={survey.observations.sales_prev} onChange={(v) => setObs("sales_prev", v)} />
                  <NumberField id="channels" label="판매채널 수" unit="개" help="매장·배달앱·온라인몰 등"
                    value={survey.observations.channels} onChange={(v) => setObs("channels", v)} />
                  <NumberField id="staff" label="직원 수" unit="명, 점주 제외" value={survey.observations.staff}
                    onChange={(v) => setObs("staff", v)} />
                  <NumberField id="benchmark" label="비교하고 싶은 월매출" unit="만원"
                    help="직접 아는 참고값만 넣으세요. 공식 업종 평균으로 표시하지 않습니다."
                    value={survey.benchmark?.monthly_sales ?? null} onChange={setBenchmark} />
                </div>
              </>
            )}
          </div>

          {warn && (
            <div className={`warn-box${warn.required.length ? " error" : ""}`} role="alert">
              {warn.required.length ? (
                <p>필수 항목 {warn.required.length}개를 입력해야 다음으로 넘어갈 수 있습니다. 빨간 테두리 항목을 확인하세요.</p>
              ) : (
                <>
                  <p>
                    {current.kind === "finance"
                      ? `비워 둔 비용 항목이 ${warn.optional.length}개 있습니다. 비운 항목은 0원으로 계산합니다.`
                      : `응답하지 않은 문항이 ${warn.optional.length}개 있습니다. 미응답은 0점이 아니라 빈칸으로 처리되지만, 응답이 많을수록 결과가 정확합니다.`}
                  </p>
                  <div className="warn-actions">
                    <button className="btn btn-line btn-sm" onClick={() => setWarn(null)}>입력하러 가기</button>
                    <button className="btn btn-dark btn-sm" onClick={() => next(true)}>그대로 진행</button>
                  </div>
                </>
              )}
            </div>
          )}

          <div className="survey-bar">
            <div className="bar-progress">
              <div className="bar-label">
                <span>진행률 <b>{pct}%</b></span>
                <span className="saved">{savedAt ? `이 기기에 자동 저장됨 · ${hhmm(savedAt)}` : "아직 저장 안 됨"}</span>
              </div>
              <div className="bar-track"><i style={{ width: `${pct}%` }} /></div>
            </div>
            <div className="bar-actions">
              <button className="btn btn-line btn-sm" onClick={() => goTo(safeStep - 1)} disabled={safeStep === 0}>이전</button>
              <button className="btn btn-line btn-sm" onClick={saveNow}>중간저장</button>
              <button className="btn btn-primary btn-sm" onClick={() => next()}>
                {isLast ? "결과 보기" : "optional" in current && current.optional ? "다음 (건너뛰기 가능)" : "다음"}
              </button>
            </div>
          </div>
        </div>
      </div>
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}

/** 입력 중에 보여 주는 계산 미리보기. 판정은 하지 않고 덧셈·뺄셈만 한다(위험 판정은 엔진이 한다). */
function FinancePreview({ survey }: { survey: Survey }) {
  const f = survey.finance;
  const sales = f.monthly_sales;
  if (typeof sales !== "number") return null;
  const cost = [f.material_cost, f.labor_cost, f.rent, f.other_cost].reduce<number>((a, v) => a + (typeof v === "number" ? v : 0), 0);
  const residual = sales - cost;
  return (
    <div className="finance-preview" aria-live="polite">
      <div><small>비용 합계</small><b>{cost.toLocaleString("ko-KR")}만원</b></div>
      <div><small>영업잔여액 (매출 − 비용)</small><b className={residual < 0 ? "neg" : ""}>{residual.toLocaleString("ko-KR")}만원</b></div>
      <p>영업잔여액은 세무·회계상 영업이익이 아닙니다.</p>
    </div>
  );
}
