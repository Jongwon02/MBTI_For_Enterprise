# Biz-DNA 1.0 엔진 동작 명세 (시제품 소스 기준)

출처: ChatGPT 대화에 남아 있는 `bizdna/engine.py`, `create_examples.py`, `test_engine.py`(1.0), `BizDNA_Integrated/reports.py`, `api.py`(2.0) 원문. 원본은 `legacy/`에 있다. 2026-11-15에 로컬에서 실행해 PRD 8.7의 결과값(61.87, 75.16, 추천 순위)이 재현되는 것을 확인했다(`legacy/README.md`).

## 1. 입력 JSON

```json
{
  "company": {"name": "그린푸드랩", "industry": "식품제조"},
  "answers": {
    "dna":        {"D01": 1~5, ..., "D24": 1~5},
    "competence": {"A01": 1~5, ..., "H08": 1~5},
    "stage": {"product": 1~5, "customer": 1~5, "revenue": 1~5,
              "cash": 1~5, "operations": 1~5, "expansion": 1~5}
  },
  "goals": ["profit", "market", "product", "scale", "funding", "stability" 중 선택],
  "flags": {"cash_crisis": bool, "market_unvalidated": bool, "negative_unit_margin": bool,
            "founder_bottleneck": bool, "capacity_shortage": bool, "funding_gap": bool,
            "service_overload": bool}
}
```

- DNA 문항과 역량 문항은 `answers.dna` / `answers.competence`로 네임스페이스가 나뉘어 있어, 재무 문항 `D01~D08`과 DNA 문항 `D01~D24`가 엔진 안에서는 충돌하지 않는다. 문항 마스터를 DB 한 테이블에 둘 때는 고유 코드가 필요하다.
- **미응답·범위 밖 값은 `DiagnosticError`로 거부**한다. PRD의 "미응답은 결측 처리"와 다르다.
- 성장계획 P01~P12 문항은 엔진 입력에 없다. `goals`와 `flags`가 그 역할을 대신한다.

## 2. DNA

- 축별 6문항: D01~06 G/S, D07~12 I/E, D13~18 N/C, D19~24 P/O
- `score = Σ(x−1)/24×100` (소수 2자리), **문자는 항상 50 기준**(≥50 → A 성향), `boundary = 40 < score < 60`
- 역채점은 구현돼 있지 않다.

## 3. 8대 역량

- `C_d = Σ(x−1)/32×100`, `T = Σ W_d·C_d` (가중치 A .15, B .15, C .15, D .15, E .10, F .10, G .05, H .15)
- A~E 등급 산출은 엔진에 없다(보고서에서도 미사용).

## 4. 성장단계

- 가중지수 `I = .20 product + .20 customer + .20 revenue + .15 cash + .15 operations + .10 expansion`
- 잠정단계 `= clamp(int(I + 0.5), 1, 5)`
- Gate를 아래 순서로 적용한다(위에서 내려간 단계에 다음 규칙이 이어서 적용됨).
  1. 단계 ≥ 4 이고 (customer < 4 또는 revenue < 4 또는 operations < 3) → 3
  2. 단계 ≥ 5 이고 (operations < 4 또는 expansion < 4) → 4
  3. 단계 ≥ 3 이고 (customer < 3 또는 revenue < 2) → 2
  4. 단계 ≥ 2 이고 product < 2 → 1
- 출력에 `gate_adjusted`(잠정단계와 달라졌는지)를 남긴다.

## 5. 위험요인

`flags`의 참 값을 그대로 옮긴다. 응답에서 위험을 계산하지 않는다.

| flag | 표시명 |
| --- | --- |
| cash_crisis | 현금흐름 위험 |
| market_unvalidated | 시장검증 미완료 |
| negative_unit_margin | 단위경제성 악화 |
| founder_bottleneck | 창업자 의존 |
| capacity_shortage | 공급능력 부족 |
| funding_gap | 성장자금 부족 |
| service_overload | 서비스 운영부담 (PRD 6개 규칙에 없는 7번째) |

## 6. 전략추천

전략별 연계 역량 가중치:

| 코드 | 전략 | 연계 역량 |
| --- | --- | --- |
| ST01 | 사업모델 검증 | A .45, B .40, H .15 |
| ST02 | 제품시장 적합성 확보 | B .50, C .35, A .15 |
| ST03 | 시장·판로 확대 | B .55, A .15, H .30 |
| ST04 | 브랜드·마케팅 고도화 | B .80, G .20 |
| ST05 | 기술·제품 혁신 | C .80, H .20 |
| ST06 | 수익구조 개선 | D .65, F .25, A .10 |
| ST07 | 재무구조 및 자금관리 | D .90, A .10 |
| ST08 | 조직·인재 역량 강화 | E .85, A .15 |
| ST09 | 생산·운영체계 고도화 | F .80, E .20 |
| ST10 | 디지털전환·AI 활용 | G .75, F .25 |
| ST11 | 투자유치·스케일업 | D .35, H .35, A .30 |
| ST12 | 신사업·사업전환 | A .40, C .30, H .30 |

목표 → 전략 대응(`GOAL_MATCH`): profit → ST06·07·09, market → ST03·04·02, product → ST05·02·12, scale → ST08·09·11·03, funding → ST07·11, stability → ST06·07·08

점수 구성(각 0~100):

- **U 시급성** = Σ (100 − 연계역량 점수) × 연계 가중치
- **F 적합성** = min(100, 40 + 25 × 일치 목표 수) (+10: ST08 & founder_bottleneck)
- **E 기대효과** = min(100, 45 + 20 × 일치 목표 수) (+10: ST06 & negative_unit_margin)
- **X 실행가능성** = 75 고정
- `R = .30F + .30U + .25E + .15X`

> 설계안의 F는 "유형·단계·목표 적합성"이지만 1.0은 **목표 일치만 반영하고 DNA 유형은 전략점수에 쓰지 않는다.** 단계는 아래 보류 규칙에서만 쓴다.

보류(deferred)와 가산 규칙:

| 조건 | 효과 |
| --- | --- |
| cash_crisis | ST03·05·11·12 보류 |
| market_unvalidated | ST03·04·11 보류 |
| capacity_shortage | ST03 보류 |
| negative_unit_margin | ST03·11 보류, ST06 시급성 +25 |
| founder_bottleneck | ST08 시급성 +25 |
| service_overload | ST09·10 시급성 +25 |
| funding_gap | ST07 시급성 +20 |
| 단계 ≤ S2 | ST03·11 보류 |

정렬: 추천 전략 먼저, 그 안에서 점수 내림차순, 같으면 코드 순. `top_recommended`는 보류 제외 상위 5개다.

## 7. 기준 테스트 사례 입력 (`create_examples.py`)

목표 점수를 정수 응답으로 바꿔 만든다(축별 합 `round(6 + s/100×24)`, 영역별 합 `round(8 + s/100×32)`을 1점에서 시작해 번갈아 1씩 올려 배분).

| 항목 | case_a 그린푸드랩 (식품제조) | case_b 넥스트솔루션 (B2B SaaS) |
| --- | --- | --- |
| DNA 목표(G,I,N,P축) | 78, 82, 35, 30 | 92, 88, 85, 38 |
| 역량 목표 A~H | 65, 55, 85, 45, 40, 70, 45, 75 | 80, 85, 90, 65, 50, 65, 80, 75 |
| stage | product 4, customer 3, revenue 3, cash 2, operations 3, expansion 3 | product 5, customer 4, revenue 5, cash 4, operations 3, expansion 4 |
| goals | profit, market, funding | scale, market |
| flags | negative_unit_margin, founder_bottleneck, funding_gap | founder_bottleneck, service_overload |

1.0 자동 테스트 6개: case_a → GICO·S3·ST06이 상위 추천에 포함 / case_b → GINO·S4·1순위 ST08 / D01 누락 시 오류 / 범위 밖 값 오류 / case_b customer=2 → S2 이하 / case_b cash_crisis → ST11 보류.

## 8. 보고서(2.0) 참고값

- ReportLab, A4, 한글 폰트 NanumSquare(R/B)
- 색상: NAVY `#17344D`, BLUE `#2769A0`, TEAL `#0D838B`, LIGHT `#EFF5F8`, GRAY `#5C6E7A`
- 기본형은 표지·요약과 01~05장, 정밀형은 06~15장을 더한다. 전략별 실행과제 2개(`ACTIONS`)와 KPI 2개(`KPIS`) 사전이 있다.
- AI: `OPENAI_API_KEY`가 있고 정밀형에서 요청할 때만 쓴다. 모델 `gpt-4.1-mini`(환경변수 `BIZDNA_AI_MODEL`). company·dna·competence·stage·risks·상위 3전략·goals만 보낸다. 프롬프트는 "제공된 JSON 사실만 사용, 점수·유형·우선순위 수정 금지, 수치 창작 금지, 600~900자".
- API: `POST /diagnose`(입력 JSON) → 결과 JSON, `POST /report` `{payload, mode: basic|advanced, use_ai}` → PDF

## 9. 이후 버전(범위 밖, 참고)

v3~v8은 소상공인용이다. Streamlit 화면, SQLite 저장(v6, "데모 전용·다중 사용자 운영용 아님"), 실행과제·성과추적(v7), 모바일 반응형과 GitHub + Streamlit Community Cloud 배포 안내(v8)가 있다. v8은 노출 위험 때문에 DB 기능을 빼고 체험용으로 만들었다.
