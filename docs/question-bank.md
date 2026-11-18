# Biz-DNA item bank: 100 items (verbatim from the design document)

Source: ChatGPT conversation "Biz-DNA 창업·성장기업 경영진단모형 개발 기본설계(안) v1.0", chapter Ⅳ. **Item wording is kept verbatim in Korean** (it is also the on-screen copy). There is no scoring rubric yet (per-answer 1–5 criteria, evidence, reverse scoring, industry conditions).

## A. DNA type diagnosis — 24 items

Each item is a relative choice **left tendency (1) ↔ right tendency (5)**. All 24 items currently have the A tendency (G, I, N, P) on the right, so there are no reverse items (a PRD section 13 inconsistency — consider flipping some).

| Code | Axis | Left tendency (1) ↔ right tendency (5) |
| --- | --- | --- |
| D01 | S↔G | 안정적 수익 확보 ↔ 적극적 매출 확대 |
| D02 | S↔G | 기존 사업 유지 ↔ 신규 사업 투자 |
| D03 | S↔G | 재무안정 우선 ↔ 성장기회 투자 우선 |
| D04 | S↔G | 현재 인력·조직 유지 ↔ 인력·조직 확대 |
| D05 | S↔G | 시장변화에 신중 대응 ↔ 시장기회 선제 대응 |
| D06 | S↔G | 현재 고객 기반 유지 ↔ 고객 규모 적극 확대 |
| D07 | E↔I | 원가·가격 경쟁력 ↔ 제품·서비스 차별화 |
| D08 | E↔I | 기존 기술 활용 ↔ 신규 기술 개발 |
| D09 | E↔I | 운영효율 개선 ↔ 새로운 고객가치 창출 |
| D10 | E↔I | 표준화된 제품 확대 ↔ 차별화 제품 확대 |
| D11 | E↔I | 생산성·비용절감 투자 ↔ 연구개발·혁신 투자 |
| D12 | E↔I | 검증된 사업방식 활용 ↔ 새로운 사업방식 실험 |
| D13 | C↔N | 기존 고객 심화 ↔ 신규 고객 발굴 |
| D14 | C↔N | 현재 시장점유율 확대 ↔ 새로운 시장 진출 |
| D15 | C↔N | 기존 유통채널 강화 ↔ 신규 유통채널 개척 |
| D16 | C↔N | 주력 고객군 집중 ↔ 고객군 다변화 |
| D17 | C↔N | 기존 지역·국내시장 집중 ↔ 신규 지역·해외시장 진출 |
| D18 | C↔N | 기존 제품의 반복판매 ↔ 새로운 수요시장 발굴 |
| D19 | O↔P | 창업자 직접 의사결정 ↔ 조직별 권한위임 |
| D20 | O↔P | 창업자 경험 중심 판단 ↔ 데이터·규정 중심 판단 |
| D21 | O↔P | 창업자 직접 고객관리 ↔ 전담조직 중심 고객관리 |
| D22 | O↔P | 개인별 탄력적 업무처리 ↔ 표준화된 업무체계 |
| D23 | O↔P | 창업자 직접 인력관리 ↔ 관리자·팀장 중심 관리 |
| D24 | O↔P | 창업자 주도 사업계획 ↔ 조직 참여형 사업계획 |

Screen item example (D1 growth orientation): "향후 3년간 우리 기업이 우선적으로 추구할 경영방향은 무엇입니까?" — left "안정적 수익과 재무건전성 확보", right "매출·시장점유율 확대를 위한 적극적 투자". Scale labels: 1 안정경영을 매우 중시 / 2 다소 중시 / 3 양쪽을 비슷하게 중시 / 4 성장확장을 다소 중시 / 5 매우 중시.

## B. Eight management competences — 64 items (1–5)

Some items link to evidence such as business plans, financial statements, customer data, and certificates. The design document numbers the finance domain D25–D32, but the 1.0 engine receives it as `D01–D08` inside `answers.competence` (the table uses engine keys; design codes in parentheses).

### A. 경영전략 및 비즈니스모델 — strategy & business model (15%)
| Code | Item |
| --- | --- |
| A01 | 기업의 중장기 비전과 성장목표가 구체적으로 설정되어 있는가? |
| A02 | 목표고객과 고객에게 제공하는 핵심가치가 명확한가? |
| A03 | 주요 매출원과 수익창출 구조가 검증되어 있는가? |
| A04 | 경쟁기업 대비 차별화된 사업전략을 보유하고 있는가? |
| A05 | 연간 사업계획과 핵심 성과목표를 수립하고 있는가? |
| A06 | 사업계획의 실행실적을 정기적으로 점검하고 있는가? |
| A07 | 시장환경 변화에 따라 사업전략을 조정하고 있는가? |
| A08 | 성장목표 달성을 위한 우선투자 분야를 설정하고 있는가? |

### B. 시장·고객·마케팅 — market, customer & marketing (15%)
| Code | Item |
| --- | --- |
| B01 | 목표시장 규모와 성장성을 객관적으로 파악하고 있는가? |
| B02 | 목표고객의 요구와 구매결정 요인을 파악하고 있는가? |
| B03 | 실제 고객을 대상으로 제품·서비스의 시장성을 검증하였는가? |
| B04 | 경쟁제품 대비 고객이 선택할 만한 차별성이 있는가? |
| B05 | 신규고객을 확보할 수 있는 마케팅 채널을 보유하고 있는가? |
| B06 | 고객의 재구매·재이용 및 유지현황을 관리하고 있는가? |
| B07 | 마케팅 비용 대비 고객획득 성과를 분석하고 있는가? |
| B08 | 신규시장·판로 진출을 위한 실행계획이 마련되어 있는가? |

### C. 제품·서비스·기술 — product, service & technology (15%)
| Code | Item |
| --- | --- |
| C01 | 제품·서비스의 핵심기능과 고객가치가 명확한가? |
| C02 | 제품·서비스가 실제 고객에게 제공 가능한 수준인가? |
| C03 | 고객의 사용평가를 제품개선에 반영하고 있는가? |
| C04 | 경쟁제품 대비 품질·기능·가격 등의 차별성이 있는가? |
| C05 | 핵심기술·노하우 또는 전문역량을 확보하고 있는가? |
| C06 | 제품개발 및 개선을 위한 내부 역량이나 협력체계가 있는가? |
| C07 | 지식재산·브랜드 등 핵심자산의 보호·활용체계를 갖추고 있는가? |
| C08 | 향후 신제품·서비스 고도화 계획이 구체적인가? |

### D. 재무 및 자금관리 — finance & funding (15%)
| Code | Item |
| --- | --- |
| D01 (D25) | 매출·비용·손익을 정기적으로 관리하고 있는가? |
| D02 (D26) | 제품·서비스별 원가와 수익성을 파악하고 있는가? |
| D03 (D27) | 향후 6~12개월 현금유입·유출을 예측하고 있는가? |
| D04 (D28) | 고정비 및 손익분기점 수준을 파악하고 있는가? |
| D05 (D29) | 매출채권·재고·지급채무 등 운전자금을 관리하고 있는가? |
| D06 (D30) | 차입금·이자·상환일정을 체계적으로 관리하고 있는가? |
| D07 (D31) | 성장계획에 필요한 투자자금 규모와 조달방안이 구체적인가? |
| D08 (D32) | 매출 감소나 자금부족 상황에 대한 대응계획이 있는가? |

### E. 조직 및 창업팀 — organization & founding team (10%)
| Code | Item |
| --- | --- |
| E01 | 창업자·경영자가 해당 사업의 전문성을 보유하고 있는가? |
| E02 | 핵심 사업기능을 수행할 인력이나 외부 협력역량이 확보되어 있는가? |
| E03 | 조직 내 역할과 책임이 명확하게 구분되어 있는가? |
| E04 | 핵심인력의 이탈위험과 대체방안을 관리하고 있는가? |
| E05 | 성장계획에 따른 인력확보 계획이 마련되어 있는가? |
| E06 | 업무성과를 평가하고 개선하는 체계가 있는가? |
| E07 | 조직 내 정보공유와 협업이 원활하게 이루어지는가? |
| E08 | 창업자에게 집중된 업무를 조직적으로 분산할 수 있는가? |

### F. 생산·운영·품질관리 — production, operations & quality (10%)
| Code | Item |
| --- | --- |
| F01 | 핵심 제품·서비스의 제공과정이 체계적으로 정립되어 있는가? |
| F02 | 고객수요 증가에 대응할 수 있는 공급능력을 보유하고 있는가? |
| F03 | 업무별 비용·시간·생산성을 관리하고 있는가? |
| F04 | 제품·서비스 품질을 일정 수준으로 유지하고 있는가? |
| F05 | 공급업체·협력사와의 거래위험을 관리하고 있는가? |
| F06 | 재고·납기·서비스 제공일정을 체계적으로 관리하고 있는가? |
| F07 | 운영상 오류·불량·고객불만을 분석하고 개선하는가? |
| F08 | 사업규모 확대에 필요한 운영표준과 관리체계가 있는가? |

### G. 디지털 및 데이터 활용 — digital & data (5%)
| Code | Item |
| --- | --- |
| G01 | 매출·고객·재고 등 주요 경영정보를 디지털로 관리하는가? |
| G02 | 경영 의사결정에 객관적인 데이터를 활용하는가? |
| G03 | 고객·마케팅 성과를 데이터로 분석하는가? |
| G04 | 회계·영업·운영 업무에 적합한 디지털 도구를 활용하는가? |
| G05 | 반복업무의 자동화 또는 AI 활용을 검토·추진하고 있는가? |
| G06 | 디지털 시스템 간 데이터 연계가 가능한가? |
| G07 | 주요 경영데이터의 보안·백업·접근권한을 관리하는가? |
| G08 | 디지털전환을 위한 인력·예산·추진계획이 있는가? |

### H. 성장잠재력 및 사업확장 — growth potential & expansion (15%)
| Code | Item |
| --- | --- |
| H01 | 향후 3년간 구체적인 매출·고용·시장확대 목표가 있는가? |
| H02 | 목표시장에 지속적인 성장기회가 존재하는가? |
| H03 | 사업규모 확대 시 단위당 수익성이 유지·개선될 가능성이 있는가? |
| H04 | 새로운 고객·지역·유통채널로 확장할 가능성이 있는가? |
| H05 | 성장에 필요한 핵심인력·기술·시설 등을 확보할 수 있는가? |
| H06 | 성장투자에 필요한 자금조달 가능성을 검토하였는가? |
| H07 | 향후 성장에 영향을 미칠 핵심 위험요인을 파악하고 있는가? |
| H08 | 성장목표 달성을 위한 단계별 실행계획이 마련되어 있는가? |

## C. Growth plan and execution constraints — 12 items (not scored)

Used only as goals and constraints for strategy recommendation. The design document has no option lists (draft options are in `questions_v1.json`).

| Code | Item | Response format |
| --- | --- | --- |
| P01 | 향후 3년간 가장 중요한 경영목표 | multi-select, prioritized |
| P02 | 향후 3년 목표 매출액 | amount |
| P03 | 향후 3년 목표 고용인원 | headcount |
| P04 | 향후 1년간 계획된 투자규모 | amount |
| P05 | 우선 투자희망 분야 | multi-select |
| P06 | 향후 1년간 필요한 외부자금 | amount |
| P07 | 향후 추진할 신규제품·서비스 | plan stage (single) |
| P08 | 신규시장·해외시장 진출계획 | plan stage (single) |
| P09 | 현재 가장 심각한 성장장애 | up to 3 |
| P10 | 성장계획 실행을 위한 핵심 부족자원 | up to 3 |
| P11 | 향후 6개월 내 실행 가능한 개선과제 | up to 3 |
| P12 | 외부 컨설팅·정책지원이 필요한 분야 | prioritized choice |

## Not in the design document (filled with drafts in `questions_v1.json`)

- **Question wording and per-level criteria** for rating the 6 growth-stage indicators (commercialization, customer validation, revenue trend, profit/cash, organization/operations, market expansion) on 1–5. The 1.0 engine takes these 6 values directly.
- **Rules deriving** the 7 risk flags (`cash_crisis` etc.) from answers. The 1.0 engine takes true/false values directly.
- Mapping of P01 goal options to engine goal codes (`profit`, `market`, `product`, `scale`, `funding`, `stability`).
- The item subset used for the basic diagnosis.
