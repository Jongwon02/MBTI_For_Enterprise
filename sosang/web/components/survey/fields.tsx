"use client";

import { useMemo, useState } from "react";
import type { DnaItem, Industries, Likert } from "@/lib/types";

// 중소경영 components/survey/fields.tsx의 ScaleButtons·DnaQuestion·CompetenceQuestion을 복사해 고쳤다.

export const SCALE_LABELS = ["전혀 아니다", "아니다", "보통", "그렇다", "매우 그렇다"];
export const DNA_LABELS = ["왼쪽에 가깝다", "약간 왼쪽", "중간", "약간 오른쪽", "오른쪽에 가깝다"];

export function ScaleButtons({ name, value, labels, onChange }: {
  name: string; value?: number; labels: string[]; onChange: (v: Likert) => void;
}) {
  return (
    <div className="scale" role="radiogroup" aria-label={name}>
      {([1, 2, 3, 4, 5] as const).map((v) => (
        <button
          key={v}
          type="button"
          role="radio"
          aria-checked={value === v}
          aria-label={`${v}점 · ${labels[v - 1]}`}
          className={`scale-btn${value === v ? " on" : ""}`}
          onClick={() => onChange(v)}
        >
          <b>{v}</b>
          <small>{labels[v - 1]}</small>
        </button>
      ))}
    </div>
  );
}

export function DnaQuestion({ item, value, missing, onChange }: {
  item: DnaItem; value?: number; missing: boolean; onChange: (v: Likert) => void;
}) {
  return (
    <div className={`q-row dna-row${missing ? " missing" : ""}`} id={`q-${item.code}`}>
      <span className="q-code">{item.code}</span>
      <div className="dna-pair">
        <span className={`dna-side left${value && value <= 2 ? " lean" : ""}`}>{item.left}</span>
        <ScaleButtons name={`${item.left} 또는 ${item.right}`} value={value} labels={DNA_LABELS} onChange={onChange} />
        <span className={`dna-side right${value && value >= 4 ? " lean" : ""}`}>{item.right}</span>
      </div>
    </div>
  );
}

export function LikertQuestion({ code, text, value, missing, onChange }: {
  code: string; text: string; value?: number; missing: boolean; onChange: (v: Likert) => void;
}) {
  return (
    <div className={`q-row comp-row${missing ? " missing" : ""}`} id={`q-${code}`}>
      <div className="q-head"><span className="q-code">{code}</span><p>{text}</p></div>
      <ScaleButtons name={text} value={value} labels={SCALE_LABELS} onChange={onChange} />
    </div>
  );
}

const toNumber = (raw: string): number | null => (raw === "" ? null : Number(raw));

export function NumberField({ id, label, unit, help, value, required, missing, min = 0, max, step = 1, onChange }: {
  id: string; label: string; unit?: string; help?: string; value?: number | null; required?: boolean; missing?: boolean;
  min?: number; max?: number; step?: number; onChange: (v: number | null) => void;
}) {
  return (
    <div className={`field${missing ? " missing" : ""}`} id={`q-${id}`}>
      <label htmlFor={`f-${id}`}>
        <span className="field-label">{label}{required && <em className="req">필수</em>}{unit && <small> ({unit})</small>}</span>
      </label>
      <input id={`f-${id}`} type="number" inputMode="decimal" min={min} max={max} step={step}
        value={typeof value === "number" && Number.isFinite(value) ? value : ""}
        onChange={(e) => onChange(toNumber(e.target.value))} />
      {help && <small className="field-help">{help}</small>}
    </div>
  );
}

export function TextField({ id, label, value, placeholder, onChange }: {
  id: string; label: string; value?: string; placeholder?: string; onChange: (v: string) => void;
}) {
  return (
    <div className="field" id={`q-${id}`}>
      <label htmlFor={`f-${id}`}><span className="field-label">{label}</span></label>
      <input id={`f-${id}`} type="text" placeholder={placeholder} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}

export function ChoiceField({ id, label, options, value, required, missing, help, onChange }: {
  id: string; label: string; options: { value: string; label: string }[]; value?: string; required?: boolean;
  missing?: boolean; help?: string; onChange: (v: string | undefined) => void;
}) {
  return (
    <div className={`field wide${missing ? " missing" : ""}`} id={`q-${id}`}>
      <span className="field-label" id={`l-${id}`}>{label}{required && <em className="req">필수</em>}</span>
      {help && <small className="field-help">{help}</small>}
      <div className="choice-list" role="radiogroup" aria-labelledby={`l-${id}`}>
        {options.map((o) => (
          <button key={o.value} type="button" role="radio" aria-checked={value === o.value}
            className={`choice${value === o.value ? " on" : ""}`}
            onClick={() => onChange(value === o.value ? undefined : o.value)}>
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/** 업종 3단계 연동 선택(대분류 → 경영모델 → 세부업종) + 검색 + 기타 직접입력 (CLAUDE.md 7장). */
export function IndustryPicker({ industries, major, model, sub, missing, onChange }: {
  industries: Industries; major?: string; model?: string; sub?: string; missing: string[];
  onChange: (v: { major?: string; biz_model?: string; sub_industry?: string }) => void;
}) {
  const [query, setQuery] = useState("");
  const models = industries.models.filter((m) => m.major === major);
  const current = industries.models.find((m) => m.code === model);
  const customSub = !!sub && !!current && !current.subs.includes(sub);
  const [typing, setTyping] = useState(customSub);

  const hits = useMemo(() => {
    const q = query.trim();
    if (!q) return [];
    const out: { major: string; model: string; sub?: string; label: string }[] = [];
    for (const m of industries.models) {
      const majorName = industries.majors.find((x) => x.code === m.major)?.name ?? "";
      if (m.name.includes(q) || majorName.includes(q)) out.push({ major: m.major, model: m.code, label: `${majorName} › ${m.name}` });
      for (const s of m.subs) if (s.includes(q)) out.push({ major: m.major, model: m.code, sub: s, label: `${majorName} › ${m.name} › ${s}` });
    }
    return out.slice(0, 8);
  }, [query, industries]);

  return (
    <div className="industry-picker field wide">
      <div className="industry-search">
        <label htmlFor="f-industry-search"><span className="field-label">업종 검색</span></label>
        <input id="f-industry-search" type="search" placeholder="예: 카페, 미용, 편의점" value={query} onChange={(e) => setQuery(e.target.value)} />
        {hits.length > 0 && (
          <ul className="search-hits" role="listbox" aria-label="검색 결과">
            {hits.map((h) => (
              <li key={h.label}>
                <button type="button" onClick={() => { onChange({ major: h.major, biz_model: h.model, sub_industry: h.sub }); setTyping(false); setQuery(""); }}>
                  {h.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={`picker-step${missing.includes("major") ? " missing" : ""}`} id="q-major">
        <span className="field-label">1. 대분류<em className="req">필수</em></span>
        <div className="choice-list" role="radiogroup" aria-label="대분류">
          {industries.majors.map((m) => (
            <button key={m.code} type="button" role="radio" aria-checked={major === m.code}
              className={`choice${major === m.code ? " on" : ""}`}
              onClick={() => { onChange({ major: m.code, biz_model: undefined, sub_industry: undefined }); setTyping(false); }}>
              {m.name}
            </button>
          ))}
        </div>
        {major && <small className="field-help">{industries.majors.find((m) => m.code === major)?.examples}</small>}
      </div>

      {major && (
        <div className={`picker-step${missing.includes("biz_model") ? " missing" : ""}`} id="q-biz_model">
          <span className="field-label">2. 경영모델<em className="req">필수</em></span>
          <div className="choice-list" role="radiogroup" aria-label="경영모델">
            {models.map((m) => (
              <button key={m.code} type="button" role="radio" aria-checked={model === m.code}
                className={`choice${model === m.code ? " on" : ""}`}
                onClick={() => { onChange({ major, biz_model: m.code, sub_industry: undefined }); setTyping(false); }}>
                {m.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {current && (
        <div className="picker-step" id="q-sub_industry">
          <span className="field-label">3. 세부업종 <small>(선택)</small></span>
          <div className="choice-list" role="radiogroup" aria-label="세부업종">
            {current.subs.map((s) => (
              <button key={s} type="button" role="radio" aria-checked={!typing && sub === s}
                className={`choice${!typing && sub === s ? " on" : ""}`}
                onClick={() => { onChange({ major, biz_model: model, sub_industry: sub === s ? undefined : s }); setTyping(false); }}>
                {s}
              </button>
            ))}
            <button type="button" role="radio" aria-checked={typing} className={`choice${typing ? " on" : ""}`}
              onClick={() => { setTyping(true); onChange({ major, biz_model: model, sub_industry: undefined }); }}>
              기타 직접입력
            </button>
          </div>
          {typing && (
            <input className="sub-input" type="text" aria-label="세부업종 직접입력" placeholder="예: 수제버거"
              value={sub ?? ""} onChange={(e) => onChange({ major, biz_model: model, sub_industry: e.target.value || undefined })} />
          )}
        </div>
      )}
    </div>
  );
}
