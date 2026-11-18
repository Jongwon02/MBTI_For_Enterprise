"use client";

import { Bar, BarChart, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AdminOverview, Count } from "@/lib/admin-types";

// 색: 단일 계열은 포인트 파랑, 축 방향은 A 성향 파랑 / B 성향 주황(색각 검사 통과 쌍, docs/admin.md).
export const A_COLOR = "#0071e3";
export const B_COLOR = "#c2410c";
const INK_2 = "#475569";
const MUTED = "#86868b";

function BarTip({ active, payload }: { active?: boolean; payload?: { payload: { label: string; n: number; share: number } }[] }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tip">
      <b>{d.label}</b>
      <span>{d.n.toLocaleString()}건 · {(d.share * 100).toFixed(1)}%</span>
    </div>
  );
}

/** 항목별 건수(가로 막대, 단일 계열). 라벨은 축에, 값은 막대 끝에 표시한다. */
export function CountBars({ data, labels, total, max = 12, empty = "자료가 없습니다." }: {
  data: Count[]; labels?: Record<string, string>; total: number; max?: number; empty?: string;
}) {
  if (!data.length) return <p className="chart-empty">{empty}</p>;
  const shown = data.slice(0, max);
  const rest = data.slice(max).reduce((s, d) => s + d.n, 0);
  const rows = shown.map((d) => ({
    key: d.key,
    label: labels?.[d.key] ? `${d.key} ${labels[d.key]}` : d.key,
    n: d.n,
    share: total ? d.n / total : 0,
  }));
  if (rest) rows.push({ key: "_other", label: `그 밖의 ${data.length - max}개`, n: rest, share: total ? rest / total : 0 });
  const height = rows.length * 30 + 12;
  return (
    <div style={{ height }} role="img" aria-label={rows.map((r) => `${r.label} ${r.n}건`).join(", ")}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 44, bottom: 4, left: 4 }} barCategoryGap={8}>
          <XAxis type="number" hide allowDecimals={false} />
          <YAxis type="category" dataKey="label" width={150} tickLine={false} axisLine={false}
            tick={{ fill: INK_2, fontSize: 12, fontWeight: 600 }} interval={0} />
          <Tooltip content={<BarTip />} cursor={{ fill: "rgba(0,113,227,.06)" }} />
          <Bar dataKey="n" fill={A_COLOR} radius={[0, 4, 4, 0]} maxBarSize={18} isAnimationActive={false}>
            <LabelList dataKey="n" position="right" fill={INK_2} fontSize={12} fontWeight={700} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const pct = (x: number | null) => (x == null ? "-" : `${Math.round(x * 100)}%`);
const signed = (x: number | null) => (x == null ? "-" : `${x > 0 ? "+" : ""}${x.toFixed(1)}`);

/** 경영자 성향 4축: 평균 방향값(−100~+100)을 가운데에서 갈라지는 막대로. 오른쪽이 A 성향. */
export function AxisDirections({ axes }: { axes: AdminOverview["axes"] }) {
  return (
    <div className="axis-dirs">
      {axes.map((ax) => {
        const m = ax.mean ?? 0;
        const w = Math.min(Math.abs(m), 100) / 2; // 반쪽 폭(%) 기준
        const title = `${ax.name}: 평균 방향값 ${signed(ax.mean)} (축 점수 ${ax.mean == null ? "-" : (50 + ax.mean / 2).toFixed(1)}점), ` +
          `${ax.a} 성향 ${pct(ax.a_share)}, 경계 ${pct(ax.boundary_share)}, n=${ax.n}`;
        return (
          <div className="axis-dir" key={ax.axis} title={title}>
            <div className="axis-dir-head">
              <span className="axis-b"><b style={{ color: B_COLOR }}>{ax.b}</b> {ax.b_name}</span>
              <strong>{ax.name}</strong>
              <span className="axis-a">{ax.a_name} <b style={{ color: A_COLOR }}>{ax.a}</b></span>
            </div>
            <div className="axis-track" aria-hidden="true">
              <i className="axis-zone" />
              <i className="axis-mid" />
              {ax.mean != null && (
                <i className="axis-bar" style={{
                  width: `${w}%`, background: m >= 0 ? A_COLOR : B_COLOR,
                  left: m >= 0 ? "50%" : `${50 - w}%`, borderRadius: m >= 0 ? "0 4px 4px 0" : "4px 0 0 4px",
                }} />
              )}
            </div>
            <div className="axis-dir-foot">
              <span>평균 <b>{signed(ax.mean)}</b></span>
              <span>{ax.a} 성향 <b>{pct(ax.a_share)}</b></span>
              <span>경계 <b>{pct(ax.boundary_share)}</b></span>
              <span className="muted">n={ax.n}</span>
            </div>
          </div>
        );
      })}
      <p className="chart-note">막대는 평균 방향값(−100 ~ +100), 가운데 회색 띠는 경계 구간(−20 ~ +20, 축 점수 40~60)입니다.</p>
    </div>
  );
}

/** 8대 역량 영역별 점수 분포: 회색 트랙(0~100) 위에 p25~p75 띠와 중앙값 표시. */
export function DomainRanges({ domains }: { domains: AdminOverview["domains"] }) {
  if (!domains.some((d) => d.p50 != null)) return <p className="chart-empty">정밀진단 자료가 아직 없습니다.</p>;
  return (
    <div className="domain-ranges">
      {domains.map((d) => (
        <div className="domain-range" key={d.domain}
          title={`${d.domain} ${d.name}: p25 ${d.p25 ?? "-"} · 중앙값 ${d.p50 ?? "-"} · p75 ${d.p75 ?? "-"} · 평균 ${d.mean ?? "-"}`}>
          <span className="dr-label"><b>{d.domain}</b> {d.name}</span>
          <div className="dr-track" aria-hidden="true">
            {d.p25 != null && d.p75 != null && <i className="dr-band" style={{ left: `${d.p25}%`, width: `${Math.max(d.p75 - d.p25, 0.6)}%` }} />}
            {d.p50 != null && <i className="dr-mid" style={{ left: `${d.p50}%` }} />}
          </div>
          <span className="dr-value">{d.p50 != null ? d.p50.toFixed(1) : "-"}</span>
        </div>
      ))}
      <div className="domain-range dr-scale-row" aria-hidden="true">
        <span />
        <div className="dr-scale">
          {[0, 40, 55, 70, 85, 100].map((x) => <span key={x} style={{ left: `${x}%` }}>{x}</span>)}
        </div>
        <span />
      </div>
      <p className="chart-note">띠는 하위 25%~상위 25%(p25~p75), 세로선은 중앙값, 오른쪽 숫자는 중앙값입니다.</p>
    </div>
  );
}

export { MUTED };
