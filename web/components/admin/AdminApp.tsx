"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { adminExportCsv, adminFact, adminFacts, adminOverview, ApiError } from "@/lib/api";
import type { AdminFactDetail, AdminFactPage, AdminFilters, AdminOverview } from "@/lib/admin-types";
import { useAuth } from "@/lib/auth";
import { useIsAdmin } from "@/lib/useIsAdmin";
import { AxisDirections, CountBars, DomainRanges } from "./charts";
import { FactDetail } from "./FactDetail";

const PAGE = 25;
const REFRESH_MS = 15_000;
const INDUSTRIES = ["제조업", "서비스업", "도소매업"];
const STAGES = ["S1", "S2", "S3", "S4", "S5"];

const fmtDate = (iso: string) => new Date(iso).toLocaleDateString("ko-KR", { year: "2-digit", month: "2-digit", day: "2-digit" });
const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const errText = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback);

type Data = { overview: AdminOverview; page: AdminFactPage; key: string };

export function AdminApp() {
  const router = useRouter();
  const auth = useAuth();
  const isAdmin = useIsAdmin();
  const [filters, setFilters] = useState<AdminFilters>({});
  const [offset, setOffset] = useState(0);
  const [live, setLive] = useState(true);
  const [tick, setTick] = useState(0);
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<AdminFactDetail | null>(null);
  const [exporting, setExporting] = useState(false);

  const key = JSON.stringify([filters, offset]);

  useEffect(() => {
    if (auth.status === "signed-out") router.replace("/login?next=%2Fadmin");
  }, [auth.status, router]);

  // 필터·페이지가 바뀌거나 자동 갱신 주기가 돌면 다시 불러온다. setState는 응답이 온 뒤에만 한다.
  useEffect(() => {
    if (isAdmin !== true) return;
    let alive = true;
    Promise.all([adminOverview(filters), adminFacts(filters, offset, PAGE)])
      .then(([overview, page]) => {
        if (!alive) return;
        setData({ overview, page, key });
        setError(null);
      })
      .catch((e) => alive && setError(errText(e, "데이터를 불러오지 못했습니다.")));
    return () => {
      alive = false;
    };
  }, [isAdmin, filters, offset, tick, key]);

  useEffect(() => {
    if (!live || isAdmin !== true) return;
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") setTick((t) => t + 1);
    }, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [live, isAdmin]);

  const setFilter = (k: keyof AdminFilters, v: string) => {
    setFilters((f) => ({ ...f, [k]: v || undefined }));
    setOffset(0);
  };

  const openDetail = useCallback((id: string) => {
    adminFact(id)
      .then((d) => {
        setDetail(d);
        requestAnimationFrame(() => document.querySelector(".fact-detail")?.scrollIntoView({ behavior: "smooth", block: "start" }));
      })
      .catch((e) => setError(errText(e, "회차를 불러오지 못했습니다.")));
  }, []);

  const exportCsv = async () => {
    setExporting(true);
    try {
      await adminExportCsv(filters);
    } catch (e) {
      setError(errText(e, "내보내지 못했습니다."));
    }
    setExporting(false);
  };

  if (auth.status !== "signed-in" || isAdmin === null) {
    return <div className="admin-body"><div className="admin-wrap"><div className="panel loading-panel">권한을 확인하는 중입니다…</div></div></div>;
  }
  if (!isAdmin) {
    return (
      <div className="admin-body"><div className="admin-wrap">
        <div className="panel loading-panel">관리자만 볼 수 있는 화면입니다. 관리자 계정으로 로그인하세요.</div>
      </div></div>
    );
  }

  const ov = data?.overview;
  const page = data?.page;
  const labels = ov?.labels ?? null;
  const loading = !data || data.key !== key;

  return (
    <div className="admin-body">
      <div className="admin-wrap">
        {/* 필터: 한 줄, 바꾸면 바로 반영 */}
        <section className="panel admin-filters" aria-label="필터">
          <label><span>업종</span>
            <select value={filters.industry ?? ""} onChange={(e) => setFilter("industry", e.target.value)}>
              <option value="">전체</option>
              {INDUSTRIES.map((x) => <option key={x}>{x}</option>)}
            </select>
          </label>
          <label><span>진단 구분</span>
            <select value={filters.phase ?? ""} onChange={(e) => setFilter("phase", e.target.value)}>
              <option value="">전체</option><option value="basic">기본진단</option><option value="full">정밀진단</option>
            </select>
          </label>
          <label><span>성장단계</span>
            <select value={filters.stage ?? ""} onChange={(e) => setFilter("stage", e.target.value)}>
              <option value="">전체</option>
              {STAGES.map((x) => <option key={x} value={x}>{x} {labels?.stages[x.slice(1)] ?? ""}</option>)}
            </select>
          </label>
          <label><span>DNA 유형</span>
            <select value={filters.dna_type ?? ""} onChange={(e) => setFilter("dna_type", e.target.value)}>
              <option value="">전체</option>
              {Object.entries(labels?.types ?? {}).map(([k, v]) => <option key={k} value={k}>{k} {v}</option>)}
            </select>
          </label>
          <label><span>시작일</span><input type="date" value={filters.since ?? ""} onChange={(e) => setFilter("since", e.target.value)} /></label>
          <label><span>종료일</span><input type="date" value={filters.until ?? ""} onChange={(e) => setFilter("until", e.target.value)} /></label>
          <div className="admin-filter-actions">
            <button className="text-btn" onClick={() => { setFilters({}); setOffset(0); }}>필터 초기화</button>
            <label className="live-toggle">
              <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
              <span>실시간 갱신 (15초)</span>
            </label>
            <button className="btn btn-line btn-sm" onClick={() => setTick((t) => t + 1)}>새로고침</button>
            <button className="btn btn-dark btn-sm" disabled={exporting} onClick={exportCsv}>{exporting ? "내보내는 중…" : "CSV 내보내기"}</button>
          </div>
        </section>

        {error && <p className="warn-box" role="alert">{error}</p>}

        {ov && (
          <>
            <p className="admin-meta">
              {loading ? "불러오는 중…" : `마지막 갱신 ${fmtTime(ov.generated_at)}`} · 통계 활용에 동의한 회원의 최종저장 회차만 모입니다.
              기업명·이름·아이디는 저장되지 않으며, 조회 기록이 남습니다.
            </p>

            <section className="admin-kpis" aria-label="요약">
              <div className="kpi"><span>진단 회차</span><b>{ov.n.toLocaleString()}</b></div>
              <div className="kpi"><span>경영자(가명)</span><b>{ov.subjects.toLocaleString()}</b></div>
              <div className="kpi"><span>정밀진단 비율</span><b>{ov.n ? `${Math.round((ov.full / ov.n) * 100)}%` : "-"}</b></div>
              <div className="kpi"><span>종합역량 중앙값</span><b>{ov.total_score.p50 != null ? ov.total_score.p50.toFixed(1) : "-"}</b></div>
              <div className="kpi"><span>진단 시작 → 기본 완료 → 정밀 완료 <small>(전체 기간)</small></span>
                <b className="kpi-funnel">{ov.funnel.started} → {ov.funnel.basic_completed} → {ov.funnel.full_completed}</b></div>
            </section>

            <div className="admin-grid">
              <section className="panel admin-card wide">
                <h3>경영자 성향 4축 <small>평균 방향값</small></h3>
                <AxisDirections axes={ov.axes} />
              </section>
              <section className="panel admin-card">
                <h3>DNA 유형 분포</h3>
                <CountBars data={ov.dna_types} labels={labels?.types} total={ov.n} max={16} />
              </section>
              <section className="panel admin-card">
                <h3>성장단계 분포</h3>
                <CountBars data={[...ov.stages].sort((a, b) => a.key.localeCompare(b.key))}
                  labels={Object.fromEntries(STAGES.map((s) => [s, labels?.stages[s.slice(1)] ?? ""]))} total={ov.n} />
              </section>
              <section className="panel admin-card wide">
                <h3>8대 역량 점수 분포 <small>정밀진단</small></h3>
                <DomainRanges domains={ov.domains} />
              </section>
              <section className="panel admin-card">
                <h3>업종</h3>
                <CountBars data={ov.industries} total={ov.n} />
              </section>
              <section className="panel admin-card">
                <h3>추천 전략 1~3순위 빈도</h3>
                <CountBars data={ov.strategies} labels={labels?.strategies} total={ov.full || 1} />
              </section>
              <section className="panel admin-card">
                <h3>성장장애 (P09)</h3>
                <CountBars data={ov.risks} labels={labels?.risks} total={ov.n} />
              </section>
              <section className="panel admin-card">
                <h3>성장목표 (P01)</h3>
                <CountBars data={ov.goals} labels={labels?.goals} total={ov.n} />
              </section>
            </div>
          </>
        )}

        {page && (
          <section className="panel admin-table-wrap" aria-label="회차 목록">
            <div className="admin-table-head">
              <h3>회차 목록 <small>{page.total.toLocaleString()}건</small></h3>
              <div className="pager">
                <button className="text-btn" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>이전</button>
                <span>{page.total ? `${offset + 1}–${Math.min(offset + PAGE, page.total)}` : "0"}</span>
                <button className="text-btn" disabled={offset + PAGE >= page.total} onClick={() => setOffset(offset + PAGE)}>다음</button>
              </div>
            </div>
            <div className="table-scroll">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>완료일</th><th>가명</th><th>회차</th><th>구분</th><th>업종</th><th>설립</th><th>매출(억)</th><th>인력</th>
                    <th>DNA</th><th>G/S</th><th>I/E</th><th>N/C</th><th>P/O</th><th>단계</th><th>종합</th><th>추천 1~3</th>
                  </tr>
                </thead>
                <tbody>
                  {page.items.map((f) => (
                    <tr key={f.fact_id} tabIndex={0} onClick={() => openDetail(f.fact_id)}
                      onKeyDown={(e) => e.key === "Enter" && openDetail(f.fact_id)}
                      className={detail?.fact_id === f.fact_id ? "selected" : ""}>
                      <td>{fmtDate(f.completed_at)}</td>
                      <td className="mono">{f.subject_key.slice(0, 8)}</td>
                      <td>{f.round_no}</td>
                      <td>{f.phase === "full" ? "정밀" : "기본"}</td>
                      <td>{f.industry ?? "-"}</td>
                      <td>{f.founded_year ?? "-"}</td>
                      <td className="num">{f.sales_recent ?? "-"}</td>
                      <td className="num">{f.employees ?? "-"}</td>
                      <td><b>{f.dna_type ?? "-"}</b></td>
                      {[f.dna_g_dir, f.dna_i_dir, f.dna_n_dir, f.dna_p_dir].map((v, i) => (
                        <td key={i} className={`num ${v == null ? "" : v >= 0 ? "pos" : "neg"}`}>{v == null ? "-" : `${v > 0 ? "+" : ""}${Math.round(v)}`}</td>
                      ))}
                      <td>{f.stage_code ?? "-"}</td>
                      <td className="num">{f.total_score != null ? `${f.total_score.toFixed(1)} ${f.grade}` : "-"}</td>
                      <td>{f.top_strategies?.join(" · ") || "-"}</td>
                    </tr>
                  ))}
                  {!page.items.length && (
                    <tr><td colSpan={16} className="chart-empty">조건에 맞는 회차가 없습니다.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            <p className="chart-note">행을 누르면 상세를 봅니다. 방향값은 −100(B 성향) ~ +100(A 성향)이며 파랑은 A, 주황은 B 쪽입니다.</p>
          </section>
        )}

        {detail && <FactDetail fact={detail} labels={labels} onClose={() => setDetail(null)} />}
      </div>
    </div>
  );
}
