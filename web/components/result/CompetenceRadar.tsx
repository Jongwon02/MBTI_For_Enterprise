"use client";

import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from "recharts";

const SHORT: Record<string, string> = {
  A: "전략·사업모델", B: "시장·고객", C: "제품·기술", D: "재무·자금",
  E: "조직·팀", F: "생산·운영", G: "디지털", H: "성장잠재력",
};

export function CompetenceRadar({ domains }: { domains: Record<string, number | null> }) {
  const data = Object.entries(domains).map(([k, v]) => ({ domain: `${k} ${SHORT[k] ?? k}`, score: v ?? 0 }));
  return (
    <div className="radar-box" role="img" aria-label={`8대 경영역량 점수: ${data.map((d) => `${d.domain} ${d.score}점`).join(", ")}`}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="#dfe3e8" />
          <PolarAngleAxis dataKey="domain" tick={{ fill: "#334155", fontSize: 12, fontWeight: 700 }} />
          <PolarRadiusAxis domain={[0, 100]} tickCount={6} tick={{ fill: "#86868b", fontSize: 10 }} axisLine={false} angle={90} />
          <Radar dataKey="score" stroke="#0071e3" strokeWidth={2} fill="#0071e3" fillOpacity={0.18} dot={{ r: 3, fill: "#0071e3" }} isAnimationActive={false} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
