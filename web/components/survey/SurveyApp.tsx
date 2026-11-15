"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, fetchQuestions } from "@/lib/api";
import { SAMPLE_SURVEY } from "@/lib/sample";
import { clearSaved, emptySurvey, loadSaved, save } from "@/lib/storage";
import type { PlanValue, Questions, Survey } from "@/lib/types";
import { CompanyForm, CompetenceQuestion, DnaQuestion, PlanQuestion, StageQuestion } from "./fields";

type Step =
  | { id: string; group: "basic" | "full"; kind: "company"; title: string; caption: string }
  | { id: string; group: "basic" | "full"; kind: "dna"; title: string; caption: string; axis: string }
  | { id: string; group: "basic" | "full"; kind: "stage"; title: string; caption: string }
  | { id: string; group: "basic" | "full"; kind: "plan"; title: string; caption: string; phase: "basic" | "full" }
  | { id: string; group: "basic" | "full"; kind: "competence"; title: string; caption: string; domain: string };

function buildSteps(q: Questions): Step[] {
  return [
    { id: "company", group: "basic", kind: "company", title: "기업정보", caption: "업종, 업력, 매출, 인력 등 기본 정보를 입력합니다." },
    ...q.dna.axes.map((a): Step => ({ id: `dna-${a.key}`, group: "basic", kind: "dna", title: `DNA · ${a.name}`, caption: a.caption, axis: a.key })),
    { id: "stage", group: "basic", kind: "stage", title: "성장단계", caption: q.stage.prompt },
    { id: "goals", group: "basic", kind: "plan", title: "경영목표·성장장애", caption: "앞으로의 목표와 지금 가장 큰 어려움을 고릅니다.", phase: "basic" },
    ...q.competence.domains.map((d): Step => ({ id: `comp-${d.code}`, group: "full", kind: "competence", title: `${d.code}. ${d.title}`, caption: d.caption, domain: d.code })),
    { id: "plan", group: "full", kind: "plan", title: "성장계획·실행제약", caption: "성장계획과 필요한 자원을 입력합니다. 점수에는 합산하지 않습니다.", phase: "full" },
  ];
}

const isEmpty = (v: unknown) => v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);

/** 단계별 [필수 미응답, 선택 미응답] 문항 코드 */
function missingFor(step: Step, q: Questions, s: Survey): { required: string[]; optional: string[] } {
  const a = s.answers;
  switch (step.kind) {
    case "company":
      return { required: q.company_fields.filter((f) => f.required && isEmpty(s.company[f.key])).map((f) => f.key), optional: [] };
    case "dna":
      return { required: [], optional: q.dna.items.filter((i) => i.axis === step.axis && isEmpty(a.dna[i.code])).map((i) => i.code) };
    case "stage":
      return { required: q.stage.items.filter((i) => isEmpty(a.stage[i.key])).map((i) => i.key), optional: [] };
    case "competence": {
      const d = q.competence.domains.find((x) => x.code === step.domain)!;
      return { required: [], optional: d.items.filter((i) => isEmpty(a.competence[i.code])).map((i) => i.code) };
    }
    case "plan": {
      const items = q.plan.items.filter((i) => i.phase === step.phase);
      return {
        required: items.filter((i) => i.required && isEmpty(a.plan[i.code])).map((i) => i.code),
        optional: [],
      };
    }
  }
}

function countFor(step: Step, q: Questions, s: Survey): [answered: number, total: number] {
  const a = s.answers;
  switch (step.kind) {
    case "company": {
      const req = q.company_fields.filter((f) => f.required);
      return [req.filter((f) => !isEmpty(s.company[f.key])).length, req.length];
    }
    case "dna": {
      const items = q.dna.items.filter((i) => i.axis === step.axis);
      return [items.filter((i) => !isEmpty(a.dna[i.code])).length, items.length];
    }
    case "stage":
      return [q.stage.items.filter((i) => !isEmpty(a.stage[i.key])).length, q.stage.items.length];
    case "competence": {
      const d = q.competence.domains.find((x) => x.code === step.domain)!;
      return [d.items.filter((i) => !isEmpty(a.competence[i.code])).length, d.items.length];
    }
    case "plan": {
      const items = q.plan.items.filter((i) => i.phase === step.phase);
      return [items.filter((i) => !isEmpty(a.plan[i.code])).length, items.length];
    }
  }
}

export function SurveyApp() {
  const router = useRouter();
  const [q, setQ] = useState<Questions | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  // 이 컴포넌트는 브라우저에서만 렌더링되므로(SurveyClient, ssr:false) 저장된 응답을 초기값으로 바로 읽는다.
  const [initial] = useState(loadSaved);
  const [survey, setSurvey] = useState<Survey>(() => initial?.survey ?? emptySurvey());
  const [step, setStep] = useState(initial?.step ?? 0);
  const [maxStep, setMaxStep] = useState(initial?.maxStep ?? 0);
  const [basicDone, setBasicDone] = useState(initial?.basicDone ?? false);
  const [phase, setPhase] = useState<"basic" | "full">(initial?.phase ?? "basic");
  const [savedAt, setSavedAt] = useState<string | null>(initial?.savedAt ?? null);
  const [toast, setToast] = useState<string | null>(null);
  const [warn, setWarn] = useState<{ required: string[]; optional: string[] } | null>(null);
  const [confirmReset, setConfirmReset] = useState(false);

  const fetchAll = useCallback(() => {
    fetchQuestions().then(setQ).catch((e) => setLoadError(e instanceof ApiError ? e.message : "문항을 불러오지 못했습니다."));
  }, []);
  const retry = () => { setLoadError(null); fetchAll(); };

  useEffect(fetchAll, [fetchAll]);

  const steps = useMemo(() => (q ? buildSteps(q) : []), [q]);
  const basicEnd = steps.findIndex((s) => s.id === "goals");
  const current = steps[step];

  const persist = useCallback((next: Partial<{ survey: Survey; step: number; maxStep: number; basicDone: boolean; phase: "basic" | "full" }>) => {
    const at = save({
      survey: next.survey ?? survey, step: next.step ?? step, maxStep: next.maxStep ?? maxStep,
      basicDone: next.basicDone ?? basicDone, phase: next.phase ?? phase,
    });
    if (at) setSavedAt(at);
    return at;
  }, [survey, step, maxStep, basicDone, phase]);

  const update = (fn: (s: Survey) => Survey) => {
    setSurvey((prev) => {
      const next = fn(prev);
      save({ survey: next, step, maxStep, basicDone, phase });
      return next;
    });
    setSavedAt(new Date().toISOString());
    setWarn(null);
  };

  const setAnswer = (section: "dna" | "stage" | "competence", code: string, v: number) =>
    update((s) => ({ ...s, answers: { ...s.answers, [section]: { ...s.answers[section], [code]: v } } }));
  const setPlan = (code: string, v: PlanValue) =>
    update((s) => ({ ...s, answers: { ...s.answers, plan: { ...s.answers.plan, [code]: v } } }));
  const setCompany = (key: string, v: unknown) =>
    update((s) => ({ ...s, company: { ...s.company, [key]: v as never } }));

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2600);
  };

  const goTo = (i: number) => {
    setStep(i);
    setWarn(null);
    persist({ step: i });
    window.scrollTo({ top: document.getElementById("survey-top")?.offsetTop ?? 0, behavior: "smooth" });
  };

  const next = (force = false) => {
    if (!q || !current) return;
    const m = missingFor(current, q, survey);
    if (m.required.length || (m.optional.length && !force)) {
      setWarn(m);
      document.getElementById(`q-${(m.required[0] ?? m.optional[0])}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (step === basicEnd) {
      setBasicDone(true);
      setPhase("basic");
      persist({ basicDone: true, phase: "basic", step: basicEnd + 1, maxStep: Math.max(maxStep, basicEnd + 1) });
      router.push("/diagnosis/result");
      return;
    }
    if (step === steps.length - 1) {
      setPhase("full");
      persist({ phase: "full" });
      router.push("/diagnosis/result");
      return;
    }
    const n = step + 1;
    const mx = Math.max(maxStep, n);
    setMaxStep(mx);
    setStep(n);
    setWarn(null);
    persist({ step: n, maxStep: mx });
    window.scrollTo({ top: document.getElementById("survey-top")?.offsetTop ?? 0, behavior: "smooth" });
  };

  const fillSample = () => {
    setSurvey(SAMPLE_SURVEY);
    const mx = steps.length - 1;
    setMaxStep(mx);
    save({ survey: SAMPLE_SURVEY, step, maxStep: mx, basicDone, phase });
    setSavedAt(new Date().toISOString());
    showToast("가상기업(그린푸드랩) 예시 응답으로 채웠습니다.");
  };

  const reset = () => {
    clearSaved();
    setSurvey(emptySurvey());
    setStep(0); setMaxStep(0); setBasicDone(false); setPhase("basic"); setSavedAt(null); setConfirmReset(false); setWarn(null);
    showToast("응답을 모두 지웠습니다.");
  };

  if (loadError) {
    return (
      <div className="survey-body"><div className="survey-wrap single">
        <div className="panel notice-panel" role="alert">
          <h3>문항을 불러오지 못했습니다</h3>
          <p>{loadError}</p>
          <p className="muted">개발 환경에서는 api 폴더에서 <code>uvicorn bizdna_api.main:app --port 8000</code>을 실행해야 합니다.</p>
          <button className="btn btn-dark btn-sm" onClick={retry}>다시 시도</button>
        </div>
      </div></div>
    );
  }
  if (!q || !current) {
    return <div className="survey-body"><div className="survey-wrap single"><div className="panel loading-panel">문항을 불러오는 중입니다…</div></div></div>;
  }

  const group = current.group;
  const groupSteps = steps.filter((s) => s.group === group);
  const [answered, total] = groupSteps.reduce(([a, t], s) => { const [x, y] = countFor(s, q, survey); return [a + x, t + y]; }, [0, 0]);
  const pct = Math.round((answered / total) * 100);
  const missingSet = new Set(warn ? [...warn.required, ...warn.optional] : []);
  const isBasicLast = step === basicEnd;
  const isLast = step === steps.length - 1;

  return (
    <div className="survey-body" id="survey-top">
      <div className="survey-wrap">
        <aside className="survey-side" aria-label="진단 단계">
          <div className="side-inner">
            {(["basic", "full"] as const).map((g) => (
              <div className="step-group" key={g}>
                <div className="side-title">{g === "basic" ? "기본진단" : "정밀진단"}</div>
                <ol>
                  {steps.map((s, i) => s.group !== g ? null : (() => {
                    const [x, y] = countFor(s, q, survey);
                    const locked = i > maxStep;
                    return (
                      <li key={s.id}>
                        <button
                          className={`step-link${i === step ? " active" : ""}${x === y ? " done" : ""}`}
                          disabled={locked}
                          onClick={() => goTo(i)}
                          aria-current={i === step ? "step" : undefined}
                        >
                          <span className="indicator" />
                          <span className="step-name">{s.title}</span>
                          <span className="step-count">{x}/{y}</span>
                        </button>
                      </li>
                    );
                  })())}
                </ol>
              </div>
            ))}
            <div className="side-tools">
              <button className="text-btn" onClick={fillSample}>예시 기업으로 채우기</button>
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
            <span className="step-kicker">{group === "basic" ? "기본진단" : "정밀진단"} · {groupSteps.indexOf(current) + 1}/{groupSteps.length}</span>
            <h2>{current.title}</h2>
            <p>{current.caption}</p>
            {(current.kind === "stage" || (current.kind === "plan" && q.plan.draft)) && (
              <span className="draft-badge">초안 문항 · 확정 전</span>
            )}
          </div>

          <div className="panel">
            {current.kind === "company" && (
              <CompanyForm fields={q.company_fields} values={survey.company} missing={warn?.required ?? []} onChange={setCompany} />
            )}
            {current.kind === "dna" && (
              <>
                <p className="panel-prompt">{q.dna.prompt}</p>
                <div className="q-list">
                  {q.dna.items.filter((i) => i.axis === current.axis).map((i) => (
                    <DnaQuestion key={i.code} item={i} value={survey.answers.dna[i.code]} labels={q.dna.scale}
                      missing={missingSet.has(i.code)} onChange={(v) => setAnswer("dna", i.code, v)} />
                  ))}
                </div>
              </>
            )}
            {current.kind === "stage" && (
              <div className="q-list">
                {q.stage.items.map((i, idx) => (
                  <StageQuestion key={i.key} item={i} index={idx} value={survey.answers.stage[i.key]}
                    missing={missingSet.has(i.key)} onChange={(v) => setAnswer("stage", i.key, v)} />
                ))}
              </div>
            )}
            {current.kind === "competence" && (
              <>
                <p className="panel-prompt">{q.competence.prompt}</p>
                <div className="q-list">
                  {q.competence.domains.find((d) => d.code === current.domain)!.items.map((i) => (
                    <CompetenceQuestion key={i.code} code={i.code} text={i.text} value={survey.answers.competence[i.code]}
                      labels={q.scale5} missing={missingSet.has(i.code)} onChange={(v) => setAnswer("competence", i.code, v)} />
                  ))}
                </div>
              </>
            )}
            {current.kind === "plan" && (
              <div className="q-list">
                {q.plan.items.filter((i) => i.phase === current.phase).map((i) => (
                  <PlanQuestion key={i.code} item={i} value={survey.answers.plan[i.code]}
                    missing={missingSet.has(i.code)} onChange={(v) => setPlan(i.code, v)} />
                ))}
              </div>
            )}
          </div>

          {warn && (
            <div className={`warn-box${warn.required.length ? " error" : ""}`} role="alert">
              {warn.required.length ? (
                <p>필수 항목 {warn.required.length}개에 응답해야 다음으로 넘어갈 수 있습니다. 빨간 테두리 항목을 확인하세요.</p>
              ) : (
                <>
                  <p>응답하지 않은 문항이 {warn.optional.length}개 있습니다. 미응답은 0점이 아니라 결측으로 처리되지만, 응답이 많을수록 결과가 정확합니다.</p>
                  <div className="warn-actions">
                    <button className="btn btn-line btn-sm" onClick={() => setWarn(null)}>응답하러 가기</button>
                    <button className="btn btn-dark btn-sm" onClick={() => next(true)}>미응답으로 두고 진행</button>
                  </div>
                </>
              )}
            </div>
          )}

          <div className="survey-bar">
            <div className="bar-progress">
              <div className="bar-label">
                <span>{group === "basic" ? "기본진단" : "정밀진단"} 진행률 <b>{pct}%</b></span>
                <span className="saved">{savedAt ? `자동 저장됨 · ${new Date(savedAt).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })}` : "아직 저장 안 됨"}</span>
              </div>
              <div className="bar-track"><i style={{ width: `${pct}%` }} /></div>
            </div>
            <div className="bar-actions">
              <button className="btn btn-line btn-sm" onClick={() => goTo(step - 1)} disabled={step === 0}>이전</button>
              <button className="btn btn-line btn-sm" onClick={() => { if (persist({})) showToast("저장했습니다. 이 브라우저에서 이어서 진단할 수 있습니다."); else showToast("이 브라우저에서는 저장할 수 없습니다."); }}>중간저장</button>
              <button className="btn btn-primary btn-sm" onClick={() => next()}>
                {isBasicLast ? "기본진단 결과 보기" : isLast ? "정밀진단 결과 보기" : "다음"}
              </button>
            </div>
          </div>
        </div>
      </div>
      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  );
}
