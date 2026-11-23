"use client";

import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from "recharts";
import type { AreaResult } from "@/lib/types";

// 중소경영 CompetenceRadar를 복사해 고쳤다. 색은 CSS 변수(--accent)를 쓴다(색값을 컴포넌트에 두지 않는다, CLAUDE.md 3.3).
export function CompetenceRadar({ areas }: { areas: AreaResult[] }) {
  const data = areas.map((a) => ({ area: `${a.code} ${a.name}`, score: a.score ?? 0 }));
  return (
    <div className="radar-box" role="img" aria-label={`8대 경영역량 점수: ${areas.map((a) => `${a.name} ${a.score ?? "결측"}점`).join(", ")}`}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="70%">
          <PolarGrid stroke="#dfe3e8" />
          <PolarAngleAxis dataKey="area" tick={{ fill: "#334155", fontSize: 12, fontWeight: 700 }} />
          <PolarRadiusAxis domain={[0, 100]} tickCount={6} tick={{ fill: "#86868b", fontSize: 10 }} axisLine={false} angle={90} />
          <Radar dataKey="score" stroke="var(--accent)" strokeWidth={2} fill="var(--accent)" fillOpacity={0.18}
            dot={{ r: 3, fill: "var(--accent)" }} isAnimationActive={false} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
