"use client";

import type { CompanyField, PlanItem, PlanValue, Questions } from "@/lib/types";

type DnaItem = Questions["dna"]["items"][number];
type StageItem = Questions["stage"]["items"][number];

export function ScaleButtons({ name, value, labels, onChange }: {
  name: string; value?: number; labels: string[]; onChange: (v: number) => void;
}) {
  return (
    <div className="scale" role="radiogroup" aria-label={name}>
      {[1, 2, 3, 4, 5].map((v) => (
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

export function DnaQuestion({ item, value, labels, missing, onChange }: {
  item: DnaItem; value?: number; labels: string[]; missing: boolean; onChange: (v: number) => void;
}) {
  return (
    <div className={`q-row dna-row${missing ? " missing" : ""}`} id={`q-${item.code}`}>
      <span className="q-code">{item.code}</span>
      <div className="dna-pair">
        <span className={`dna-side left${value && value <= 2 ? " lean" : ""}`}>{item.left}</span>
        <ScaleButtons name={`${item.left} 또는 ${item.right}`} value={value} labels={labels} onChange={onChange} />
        <span className={`dna-side right${value && value >= 4 ? " lean" : ""}`}>{item.right}</span>
      </div>
    </div>
  );
}

export function CompetenceQuestion({ code, text, value, labels, missing, onChange }: {
  code: string; text: string; value?: number; labels: string[]; missing: boolean; onChange: (v: number) => void;
}) {
  return (
    <div className={`q-row comp-row${missing ? " missing" : ""}`} id={`q-${code}`}>
      <div className="q-head"><span className="q-code">{code}</span><p>{text}</p></div>
      <ScaleButtons name={text} value={value} labels={labels} onChange={onChange} />
    </div>
  );
}

export function StageQuestion({ item, index, value, missing, onChange }: {
  item: StageItem; index: number; value?: number; missing: boolean; onChange: (v: number) => void;
}) {
  return (
    <fieldset className={`q-row stage-row${missing ? " missing" : ""}`} id={`q-${item.key}`}>
      <legend><span className="q-code">{index + 1}</span>{item.title}</legend>
      <div className="level-list">
        {item.levels.map((text, i) => (
          <label key={i} className={`level${value === i + 1 ? " on" : ""}`}>
            <input type="radio" name={`stage-${item.key}`} checked={value === i + 1} onChange={() => onChange(i + 1)} />
            <span className="level-num">{i + 1}단계</span>
            <span>{text}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function PlanQuestion({ item, value, missing, onChange }: {
  item: PlanItem; value: PlanValue | undefined; missing: boolean; onChange: (v: PlanValue) => void;
}) {
  const head = (
    <div className="plan-head">
      <span className="q-code">{item.code}</span>
      <h4>{item.title}{item.required && <em className="req">필수</em>}</h4>
      {item.max && item.type === "multi" && <small>최대 {item.max}개</small>}
    </div>
  );
  if (item.type === "number") {
    return (
      <div className={`q-row plan-row${missing ? " missing" : ""}`} id={`q-${item.code}`}>
        {head}
        <label className="num-input">
          <input
            type="number" inputMode="decimal" min={item.min} step={item.step ?? 1}
            value={typeof value === "number" ? value : ""}
            onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
            aria-label={item.title}
          />
          {item.unit && <span>{item.unit}</span>}
        </label>
      </div>
    );
  }
  const selected = Array.isArray(value) ? value : typeof value === "string" ? [value] : [];
  const full = item.type === "multi" && item.max !== undefined && selected.length >= item.max;
  const toggle = (v: string) => {
    if (item.type === "single") return onChange(selected[0] === v ? null : v);
    onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  };
  return (
    <div className={`q-row plan-row${missing ? " missing" : ""}`} id={`q-${item.code}`}>
      {head}
      {item.help && <p className="q-help">{item.help}</p>}
      <div className="choice-list" role={item.type === "single" ? "radiogroup" : "group"} aria-label={item.title}>
        {item.options?.map((o) => {
          const on = selected.includes(o.value);
          return (
            <button
              key={o.value} type="button"
              role={item.type === "single" ? "radio" : "checkbox"} aria-checked={on}
              className={`choice${on ? " on" : ""}`}
              disabled={!on && full}
              onClick={() => toggle(o.value)}
            >
              {o.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function CompanyForm({ fields, values, missing, onChange }: {
  fields: CompanyField[]; values: Record<string, unknown>; missing: string[]; onChange: (key: string, v: unknown) => void;
}) {
  return (
    <div className="company-grid">
      {fields.map((f) => {
        const id = `company-${f.key}`;
        const v = values[f.key];
        const wide = f.type === "textarea" || f.type === "multi";
        const label = (
          <span className="field-label">
            {f.label}{f.required && <em className="req">필수</em>}{f.unit && <small> ({f.unit})</small>}
          </span>
        );
        let control;
        if (f.type === "select") {
          control = (
            <select id={id} value={typeof v === "string" ? v : ""} onChange={(e) => onChange(f.key, e.target.value || null)}>
              <option value="">선택하세요</option>
              {f.options?.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          );
        } else if (f.type === "multi") {
          const sel = Array.isArray(v) ? (v as string[]) : [];
          control = (
            <div className="choice-list" role="group" aria-labelledby={`${id}-label`}>
              {f.options?.map((o) => (
                <button key={o} type="button" role="checkbox" aria-checked={sel.includes(o)}
                  className={`choice${sel.includes(o) ? " on" : ""}`}
                  onClick={() => onChange(f.key, sel.includes(o) ? sel.filter((x) => x !== o) : [...sel, o])}>
                  {o}
                </button>
              ))}
            </div>
          );
        } else if (f.type === "textarea") {
          control = <textarea id={id} rows={3} value={typeof v === "string" ? v : ""} onChange={(e) => onChange(f.key, e.target.value)} />;
        } else if (f.type === "number") {
          control = (
            <input id={id} type="number" inputMode="decimal" min={f.min} max={f.max} step={f.step ?? 1}
              value={typeof v === "number" ? v : ""}
              onChange={(e) => onChange(f.key, e.target.value === "" ? null : Number(e.target.value))} />
          );
        } else {
          control = <input id={id} type="text" placeholder={f.placeholder} value={typeof v === "string" ? v : ""} onChange={(e) => onChange(f.key, e.target.value)} />;
        }
        return (
          <div key={f.key} className={`field${wide ? " wide" : ""}${missing.includes(f.key) ? " missing" : ""}`}>
            {f.type === "multi" ? <span id={`${id}-label`}>{label}</span> : <label htmlFor={id}>{label}</label>}
            {control}
          </div>
        );
      })}
    </div>
  );
}
