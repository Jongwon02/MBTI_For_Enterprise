# Biz-DNA 1.0 engine behavior spec (from the prototype sources)

Sources: the original `bizdna/engine.py`, `create_examples.py`, `test_engine.py` (1.0), and `BizDNA_Integrated/reports.py`, `api.py` (2.0) left in the ChatGPT conversation. Originals are in `legacy/`. Run locally on 2026-11-15, reproducing PRD 8.7's results (61.87, 75.16, recommendation order) (`legacy/README.md`).

## 1. Input JSON

```json
{
  "company": {"name": "그린푸드랩", "industry": "식품제조"},
  "answers": {
    "dna":        {"D01": 1~5, ..., "D24": 1~5},
    "competence": {"A01": 1~5, ..., "H08": 1~5},
    "stage": {"product": 1~5, "customer": 1~5, "revenue": 1~5,
              "cash": 1~5, "operations": 1~5, "expansion": 1~5}
  },
  "goals": ["any of profit", "market", "product", "scale", "funding", "stability"],
  "flags": {"cash_crisis": bool, "market_unvalidated": bool, "negative_unit_margin": bool,
            "founder_bottleneck": bool, "capacity_shortage": bool, "funding_gap": bool,
            "service_overload": bool}
}
```

- DNA and competence items are namespaced as `answers.dna` / `answers.competence`, so finance items `D01–D08` and DNA items `D01–D24` do not collide inside the engine. A single DB item-master table needs unique codes.
- **Missing or out-of-range values are rejected with `DiagnosticError`.** This differs from the PRD's "missing answers are treated as missing".
- Growth-plan items P01–P12 are not engine inputs; `goals` and `flags` take their role.

## 2. DNA

- 6 items per axis: D01–06 G/S, D07–12 I/E, D13–18 N/C, D19–24 P/O
- `score = Σ(x−1)/24×100` (2 decimals); **the letter is always decided at 50** (≥ 50 → A tendency); `boundary = 40 < score < 60`
- Reverse scoring is not implemented.

## 3. Eight competences

- `C_d = Σ(x−1)/32×100`, `T = Σ W_d·C_d` (weights A .15, B .15, C .15, D .15, E .10, F .10, G .05, H .15)
- The engine does not compute A–E grades (the report does not use them either).

## 4. Growth stage

- Weighted index `I = .20 product + .20 customer + .20 revenue + .15 cash + .15 operations + .10 expansion`
- Provisional stage `= clamp(int(I + 0.5), 1, 5)`
- Gates apply in this order (each rule applies to the stage left by the previous one):
  1. stage ≥ 4 and (customer < 4 or revenue < 4 or operations < 3) → 3
  2. stage ≥ 5 and (operations < 4 or expansion < 4) → 4
  3. stage ≥ 3 and (customer < 3 or revenue < 2) → 2
  4. stage ≥ 2 and product < 2 → 1
- Output includes `gate_adjusted` (whether it differs from the provisional stage).

## 5. Risk factors

True values of `flags` are copied as is; risks are not computed from answers.

| flag | Display label |
| --- | --- |
| cash_crisis | 현금흐름 위험 (cash-flow risk) |
| market_unvalidated | 시장검증 미완료 (market not validated) |
| negative_unit_margin | 단위경제성 악화 (negative unit economics) |
| founder_bottleneck | 창업자 의존 (founder dependence) |
| capacity_shortage | 공급능력 부족 (capacity shortage) |
| funding_gap | 성장자금 부족 (growth-funding gap) |
| service_overload | 서비스 운영부담 (service operating burden; a 7th flag not among the PRD's 6 rules) |

## 6. Strategy recommendation

Linked competence weights per strategy:

| Code | Strategy | Linked competences |
| --- | --- | --- |
| ST01 | 사업모델 검증 (business-model validation) | A .45, B .40, H .15 |
| ST02 | 제품시장 적합성 확보 (product-market fit) | B .50, C .35, A .15 |
| ST03 | 시장·판로 확대 (market and channel expansion) | B .55, A .15, H .30 |
| ST04 | 브랜드·마케팅 고도화 (brand and marketing) | B .80, G .20 |
| ST05 | 기술·제품 혁신 (technology and product innovation) | C .80, H .20 |
| ST06 | 수익구조 개선 (profit-structure improvement) | D .65, F .25, A .10 |
| ST07 | 재무구조 및 자금관리 (financial structure and funding) | D .90, A .10 |
| ST08 | 조직·인재 역량 강화 (organization and talent) | E .85, A .15 |
| ST09 | 생산·운영체계 고도화 (production and operations) | F .80, E .20 |
| ST10 | 디지털전환·AI 활용 (digital transformation, AI) | G .75, F .25 |
| ST11 | 투자유치·스케일업 (investment and scale-up) | D .35, H .35, A .30 |
| ST12 | 신사업·사업전환 (new business, pivot) | A .40, C .30, H .30 |

Goal → strategy mapping (`GOAL_MATCH`): profit → ST06/07/09, market → ST03/04/02, product → ST05/02/12, scale → ST08/09/11/03, funding → ST07/11, stability → ST06/07/08

Score components (each 0–100):

- **U urgency** = Σ (100 − linked competence score) × linked weight
- **F fit** = min(100, 40 + 25 × matched goals) (+10: ST08 & founder_bottleneck)
- **E expected impact** = min(100, 45 + 20 × matched goals) (+10: ST06 & negative_unit_margin)
- **X feasibility** = 75 fixed
- `R = .30F + .30U + .25E + .15X`

> In the design document F is "fit to type, stage, and goals", but 1.0 **uses only goal matches; the DNA type is not used in strategy scores.** The stage is used only in the deferral rules below.

Deferral and bonus rules:

| Condition | Effect |
| --- | --- |
| cash_crisis | defer ST03/05/11/12 |
| market_unvalidated | defer ST03/04/11 |
| capacity_shortage | defer ST03 |
| negative_unit_margin | defer ST03/11, ST06 urgency +25 |
| founder_bottleneck | ST08 urgency +25 |
| service_overload | ST09/10 urgency +25 |
| funding_gap | ST07 urgency +20 |
| stage ≤ S2 | defer ST03/11 |

Ordering: recommended strategies first, then score descending, ties by code. `top_recommended` is the top 5 excluding deferred.

## 7. Reference test-case inputs (`create_examples.py`)

Target scores are converted into integer answers (axis sum `round(6 + s/100×24)`, domain sum `round(8 + s/100×32)`, distributed by starting every item at 1 and adding 1 in turn).

| Item | case_a 그린푸드랩 (food manufacturing) | case_b 넥스트솔루션 (B2B SaaS) |
| --- | --- | --- |
| DNA targets (G, I, N, P axes) | 78, 82, 35, 30 | 92, 88, 85, 38 |
| Competence targets A–H | 65, 55, 85, 45, 40, 70, 45, 75 | 80, 85, 90, 65, 50, 65, 80, 75 |
| stage | product 4, customer 3, revenue 3, cash 2, operations 3, expansion 3 | product 5, customer 4, revenue 5, cash 4, operations 3, expansion 4 |
| goals | profit, market, funding | scale, market |
| flags | negative_unit_margin, founder_bottleneck, funding_gap | founder_bottleneck, service_overload |

The 6 automated 1.0 tests: case_a → GICO, S3, ST06 among top recommendations / case_b → GINO, S4, rank 1 ST08 / missing D01 raises an error / out-of-range raises an error / case_b customer=2 → S2 or below / case_b cash_crisis → ST11 deferred.

## 8. Report (2.0) reference values

- ReportLab, A4, Korean font NanumSquare (R/B)
- Colors: NAVY `#17344D`, BLUE `#2769A0`, TEAL `#0D838B`, LIGHT `#EFF5F8`, GRAY `#5C6E7A`
- The basic report has a cover, summary, and chapters 01–05; the full report adds 06–15. There are dictionaries of 2 action items (`ACTIONS`) and 2 KPIs (`KPIS`) per strategy.
- AI: used only when `OPENAI_API_KEY` exists and the full report is requested. Model `gpt-4.1-mini` (env `BIZDNA_AI_MODEL`). Sends only company, dna, competence, stage, risks, top 3 strategies, goals. Prompt: "use only facts in the given JSON; do not change scores, types, or priorities; do not invent figures; 600–900 characters".
- API: `POST /diagnose` (input JSON) → result JSON; `POST /report` `{payload, mode: basic|advanced, use_ai}` → PDF

## 9. Later versions (out of scope, reference only)

v3–v8 target small merchants. They include a Streamlit UI, SQLite storage (v6, "demo only, not for multi-user operation"), action items and performance tracking (v7), and mobile responsiveness plus GitHub + Streamlit Community Cloud deployment notes (v8). v8 removed the DB feature because of exposure risk and became a trial-only version.
