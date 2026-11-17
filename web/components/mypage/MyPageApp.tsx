"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, deleteDiagnosis, listDiagnoses } from "@/lib/api";
import { displayName, signOut, useAuth } from "@/lib/auth";
import { clearMemberDraft, FIRST_FULL_STEP } from "@/lib/storage";
import type { DiagnosisSummary } from "@/lib/types";

const STATUS_LABEL: Record<DiagnosisSummary["status"], string> = {
  draft: "진행 중",
  basic_completed: "기본진단 완료",
  full_completed: "정밀진단 완료",
};

const fmt = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : "-";

function DeleteButton({ onDelete }: { onDelete: () => Promise<void> }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  if (!confirming) return <button className="text-btn" onClick={() => setConfirming(true)}>삭제</button>;
  return (
    <span className="inline-confirm">
      삭제할까요?
      <button className="text-btn danger" disabled={busy} onClick={async () => { setBusy(true); await onDelete(); setBusy(false); setConfirming(false); }}>
        {busy ? "삭제 중…" : "삭제"}
      </button>
      <button className="text-btn" onClick={() => setConfirming(false)}>취소</button>
    </span>
  );
}

function DraftCard({ d, onDelete }: { d: DiagnosisSummary; onDelete: () => Promise<void> }) {
  const pct = d.progress?.percent ?? 0;
  return (
    <article className="diag-card">
      <div className="diag-head">
        <span className="status-badge draft">{STATUS_LABEL[d.status]}</span>
        <h4>{d.company_name || "기업명 미입력"}</h4>
        <small>중간저장 {fmt(d.updated_at)}</small>
      </div>
      <div className="diag-progress">
        <span>전체 응답률 <b>{pct}%</b></span>
        <div className="bar-track"><i style={{ width: `${pct}%` }} /></div>
      </div>
      <div className="diag-actions">
        <Link className="btn btn-primary btn-sm" href={`/diagnosis?id=${d.id}`}>이어서 진단하기</Link>
        <DeleteButton onDelete={onDelete} />
      </div>
    </article>
  );
}

function CompletedCard({ d, onDelete }: { d: DiagnosisSummary; onDelete: () => Promise<void> }) {
  const s = d.summary;
  const full = d.status === "full_completed";
  const fullInProgress = !full && (d.progress?.phase === "full" || (d.progress?.step ?? 0) > FIRST_FULL_STEP);
  return (
    <article className="diag-card">
      <div className="diag-head">
        <span className={`status-badge ${full ? "full" : "basic"}`}>{STATUS_LABEL[d.status]}</span>
        <h4>{d.company_name || "기업명 미입력"}</h4>
        <small>최종저장 {fmt(d.completed_at)}{d.model_version ? ` · 모형 ${d.model_version}` : ""}</small>
      </div>
      {s && (
        <dl className="diag-summary">
          <div><dt>DNA 유형</dt><dd><b>{s.dna_type ?? "-"}</b> {s.dna_name ?? ""}</dd></div>
          <div><dt>성장단계</dt><dd><b>{s.stage ?? "-"}</b> {s.stage_name ?? ""}</dd></div>
          <div><dt>종합역량</dt><dd>{s.total != null ? <><b>{s.total.toFixed(2)}</b>점 · {s.grade}등급</> : <span className="muted">정밀진단 후 산출</span>}</dd></div>
        </dl>
      )}
      <div className="diag-actions">
        <Link className="btn btn-dark btn-sm" href={`/diagnosis/result?id=${d.id}`}>결과 보기</Link>
        {!full && (
          <Link className="btn btn-line btn-sm" href={`/diagnosis?id=${d.id}&step=${FIRST_FULL_STEP}`}>
            {fullInProgress ? "정밀진단 이어하기" : "정밀진단 시작"}
          </Link>
        )}
        <DeleteButton onDelete={onDelete} />
      </div>
    </article>
  );
}

export function MyPageApp() {
  const router = useRouter();
  const auth = useAuth();
  const [items, setItems] = useState<DiagnosisSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    listDiagnoses().then(setItems).catch((e) => setError(e instanceof ApiError ? e.message : "진단 목록을 불러오지 못했습니다."));
  }, []);

  useEffect(() => {
    if (auth.status === "signed-in") load();
    if (auth.status === "signed-out") router.replace("/login?next=%2Fmypage");
  }, [auth.status, load, router]);

  const remove = async (id: string) => {
    try {
      await deleteDiagnosis(id);
      setItems((xs) => xs?.filter((x) => x.id !== id) ?? null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "삭제하지 못했습니다.");
    }
  };

  const logout = async () => {
    clearMemberDraft();
    await signOut();
    router.replace("/");
    router.refresh();
  };

  if (auth.status !== "signed-in") {
    return <div className="mypage-body"><div className="mypage-wrap"><div className="panel loading-panel">로그인 정보를 확인하는 중입니다…</div></div></div>;
  }

  const drafts = items?.filter((d) => d.status === "draft") ?? [];
  const done = items?.filter((d) => d.status !== "draft") ?? [];

  return (
    <div className="mypage-body">
      <div className="mypage-wrap">
        <section className="panel profile-panel">
          <div>
            <span className="step-kicker">My Page</span>
            <h2>{displayName(auth.user)} 님</h2>
            <p className="muted">{auth.user.email} · 가입 {fmt(auth.user.created_at)}</p>
          </div>
          <div className="warn-actions">
            <Link className="btn btn-primary btn-sm" href="/diagnosis?new=1">새 진단 시작</Link>
            <button className="btn btn-line btn-sm" onClick={logout}>로그아웃</button>
          </div>
        </section>

        {error && (
          <div className="warn-box error" role="alert">
            <p>{error}</p>
            <div className="warn-actions"><button className="btn btn-dark btn-sm" onClick={() => { setError(null); load(); }}>다시 시도</button></div>
          </div>
        )}

        <section className="mypage-section">
          <div className="section-head">
            <h3>진행 중인 진단 <span className="count">{drafts.length}</span></h3>
            <p>중간저장한 진단입니다. 저장한 단계부터 이어서 응답할 수 있습니다.</p>
          </div>
          {items === null && !error ? <div className="panel loading-panel">불러오는 중입니다…</div>
            : drafts.length ? <div className="diag-list">{drafts.map((d) => <DraftCard key={d.id} d={d} onDelete={() => remove(d.id)} />)}</div>
              : <div className="panel empty-panel">진행 중인 진단이 없습니다.</div>}
        </section>

        <section className="mypage-section">
          <div className="section-head">
            <h3>완료한 진단평가지 <span className="count">{done.length}</span></h3>
            <p>최종저장한 진단입니다. 저장 당시의 결과와 모형 버전으로 다시 볼 수 있고, 결과 화면에서 PDF 보고서를 받을 수 있습니다.</p>
          </div>
          {items === null && !error ? <div className="panel loading-panel">불러오는 중입니다…</div>
            : done.length ? <div className="diag-list">{done.map((d) => <CompletedCard key={d.id} d={d} onDelete={() => remove(d.id)} />)}</div>
              : (
                <div className="panel empty-panel">
                  <p>아직 최종저장한 진단이 없습니다.</p>
                  <Link className="btn btn-primary btn-sm" href="/diagnosis?new=1">진단 시작하기</Link>
                </div>
              )}
        </section>
      </div>
    </div>
  );
}
