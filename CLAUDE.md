# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 따라야 할 지침이다. 상세 요구사항의 원천은 `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md`(이하 PRD)이며, 이 문서와 PRD가 충돌하면 PRD가 우선한다. PRD를 바꾸는 결정이 생기면 PRD와 이 파일의 "결정 사항" 절을 함께 갱신한다.

## 1. 프로젝트 개요

- **서비스**: Biz-DNA(가칭). 중소기업(창업·성장기업 포함)이 온라인 진단 100문항에 답하면 **DNA 유형(16종, MBTI식 4자리 코드) · 성장단계(S1~S5) · 8대 경영역량 점수 · 우선 전략 3개 · PDF 보고서**를 받는 경영진단 웹사이트.
- **흐름**: 기업정보 입력 → 기본진단 → 정밀진단 → 결과 대시보드 → 보고서 → 90일 실행 → 3·6·12개월 재진단.
- **사용자 역할 4종**: 기업 담당자(주 사용자), 컨설턴트, 운영기관, 시스템 관리자.
- **범위 밖(구현 금지)**: 소상공인(점포) 진단, 상권·카드매출 분석, 지원사업 신청자격 판정, 외부 재무데이터 자동 연계, AI의 점수·유형 직접 산출.
- **문서 언어**: UI 문구, 주석, 커밋 메시지, 문서는 한국어. 코드 식별자(변수·함수·테이블명)는 영어.

## 2. 현재 상태 (2026-11-16)

**진단 기능이 실제로 동작한다**: 기업정보 → 기본진단(DNA 24·성장단계 6·목표/장애) → 기본 결과 → 정밀진단(역량 64·성장계획) → 결과 대시보드 → PDF(기본형·정밀형).

| 구분 | 상태 |
| --- | --- |
| 구현됨 | FR-02 기업정보, FR-03 웹 설문(기본/정밀 구분, 중간저장), FR-04 완결성 검증·결측 처리, FR-05~09 엔진, FR-10 결과 대시보드, FR-11 기본형 PDF, FR-13 정밀형 PDF(약 10쪽, 15~20쪽 목표 미달) |
| 없음 | FR-01 계정·역할, FR-12 서버 저장·이력·권한(응답은 브라우저 localStorage에만 저장), 업종별 문항 분기, FR-14 이후 전부, AI 서술(FR-20) |
| 초안(사용자 확인 필요) | 성장단계 6문항의 단계별 문구, P01~P12 선택지, P01→goals·P09→flags 매핑 (`questions_v1.json`의 `draft: true`). 기본진단 범위(= DNA+단계+P01/P09)도 임시 결정 |

- 실행: `run_dev.bat`(API 8000 + 웹 3000). 테스트: `.venv/Scripts/python -m pytest api`, `web`에서 `npx tsc --noEmit && npm run lint && npm run build`. 자세한 내용은 `README.md`.
- 참고 문서: `docs/question-bank.md`(100문항 원문), `docs/engine-v1-reference.md`(1.0 계산 규칙), `docs/design-system.md`(디자인). 출처는 ChatGPT 대화 공유 링크(https://chatgpt.com/share/6af7f207-27bc-83ee-a43b-b5e628d312d2).
- `legacy/`: 1.0·2.0 시제품 원본, 실행 검증 완료(`legacy/README.md`). 수정하지 않는다. 엔진 회귀 테스트가 이 원본과 전략 점수까지 비교한다.
- `prototype/home.html`: 승인된 메인 디자인 시안. 실제 메인은 `web/app/page.tsx`로 옮겼다.
- 대화 후반의 v3~v8과 `al/` 폴더는 **소상공인용**(범위 밖)이다. 참고하거나 재사용하지 않는다.

## 3. 기술 스택

| 영역 | 선택 | 상태 |
| --- | --- | --- |
| 진단엔진 | Python 3.12 순수 함수 패키지 `api/engine/bizdna` | 사용 중 |
| API | FastAPI + Pydantic v2 (`api/bizdna_api`) | 사용 중 |
| 프런트엔드 | **Next.js 16**(App Router, cacheComponents) + React 19 + TypeScript + Tailwind 4 | 사용 중 |
| 차트 | Recharts (역량 레이더) | 사용 중 |
| PDF | ReportLab (2.0 방식). 폰트: `BIZDNA_FONT_REGULAR/BOLD` → 맑은 고딕 → 나눔 순으로 찾음 | 사용 중 |
| DB | **Supabase** (PostgreSQL, 마이그레이션은 `supabase/migrations/*.sql`) | 결정됨 · 미구현 (11장) |
| 회원가입·로그인 | **Supabase Auth** (웹: `@supabase/ssr`, API: JWT 검증) | 결정됨 · 미구현 (11장) |
| 배포 | **Vercel** (한 프로젝트에 web + api 서비스) | 결정됨 · 미구현 (11장) |
| 테스트 | pytest (엔진·API) | 화면 테스트(Playwright)는 없음 |

**Next.js 16은 학습 데이터와 다르다.** 코드를 쓰기 전에 `web/node_modules/next/dist/docs/`의 해당 문서를 확인한다(`web/AGENTS.md`). 브라우저 저장소를 읽는 화면은 `next/dynamic`의 `ssr: false` 래퍼(`SurveyClient`, `ResultClient`)로 감싸 effect 안 setState를 피한다(eslint `react-hooks/set-state-in-effect`).

### 디렉터리 구조

```
api/engine/bizdna/  engine.py(진단·전략), survey.py(설문→엔진 입력, 완결성), config.py
  config/           model_v1.json(가중치·임계값·규칙), questions_v1.json(문항·초안 문항)
api/engine/tests/   fixtures.py(기준 사례), test_regression.py(legacy 대조), test_engine.py
api/bizdna_api/     main.py(/api/questions, /api/diagnose, /api/completeness, /api/report), report.py(PDF)
api/tests/
web/app/            page.tsx(메인), diagnosis/page.tsx(설문), diagnosis/result/page.tsx(결과), styles/*.css
web/components/     SiteHeader·SiteFooter, home/, survey/(SurveyApp, fields), result/(ResultApp, CompetenceRadar)
web/lib/            api.ts, storage.ts(localStorage), types.ts, sample.ts(그린푸드랩 예시 응답), content.ts
```

- 웹은 `/api/*`를 `next.config.ts`의 rewrites로 FastAPI(`BIZDNA_API_URL`, 기본 127.0.0.1:8000)에 넘긴다.
- 문항·가중치의 정본은 `api/engine/bizdna/config/`다. 웹은 문항을 API에서 받는다. 예외로 메인 화면의 16유형 목록(`web/lib/content.ts`)은 복사본이므로 유형명을 바꾸면 함께 고친다.
- 설문 단계 순서를 바꾸면 `web/lib/storage.ts`의 `FIRST_FULL_STEP`도 맞춘다.

## 4. 진단모형 핵심 규칙 (PRD 8장 요약 — 구현 시 반드시 지킬 것)

모든 가중치·기준점·유형은 **시범검증 전 가설값**이다. 코드에 하드코딩하지 말고 `api/engine/bizdna/config/`의 버전 관리되는 설정으로 둔다.

**기준 구현은 1.0 엔진이다.** 새 엔진은 `docs/engine-v1-reference.md`의 계산을 먼저 그대로 재현해 회귀 사례를 통과시킨 다음, PRD와 다른 점(아래 ⚠ 표시)을 하나씩 고친다. 고칠 때마다 설정 버전을 올리고 회귀 기대값이 바뀌면 이유를 기록한다.

### 4.1 문항 (100문항, 원문은 `docs/question-bank.md`)
- DNA 24문항(D01~D24, 축별 6문항), 8대 역량 64문항(영역별 8문항), 성장계획·제약 12문항(P01~P12, **점수에 합산하지 않음**, 전략추천 제약조건으로만 사용).
- **코드 체계**: 1.0 엔진은 `answers.dna.D01~D24`와 `answers.competence.A01~H08`로 네임스페이스를 나눠 충돌을 피한다(재무는 `D01~D08`, 설계안 표기는 D25~D32). 입력 JSON은 이 구조를 유지한다. DB 문항 마스터에서는 `(section, code)` 복합키로 고유하게 관리한다.
- 척도 1~5점. 역방향 문항은 `6 - 원점수`. 현재 DNA 24문항은 모두 오른쪽이 A 성향이라 역문항이 없다.
- **미응답은 0점이 아니라 결측(None)**. 결측이 있는 영역 점수는 응답 문항 기준으로 환산하고 결측 비율을 결과에 함께 기록한다. (구현됨: 1.0은 미응답을 오류로 거부했으나 현재 엔진은 결측으로 기록. 영역 전체가 결측이면 그 영역을 빼고 가중치를 다시 나눈다. 성장단계는 6지표가 모두 있어야 판정한다.)
- 성장단계 6지표 문항, P01 목표 선택지→엔진 goals, P09 성장장애→위험 flags 매핑은 **초안**으로 만들어 `questions_v1.json`에 `draft: true`로 표시했다(`api/engine/bizdna/survey.py`가 변환). P09의 `talent`, `sales_channel`은 엔진 플래그가 없어 전략점수에 반영되지 않는다. 사용자가 확정하기 전까지 이 초안 표시를 유지한다.

### 4.2 DNA 유형 (4축 → 16종)
- 축: D1 G/S(성장확장/안정내실), D2 I/E(혁신차별/효율경쟁), D3 N/C(시장개척/기존시장집중), D4 P/O(조직체계/창업자주도).
- `D_k = Σ(x_kj − 1) / 24 × 100`
- 60 이상 → A 성향, 40 이하 → B 성향, 40 초과 60 미만 → **경계**. 4자리 코드가 필요하면 50 기준으로 임시 분류하되 경계 표시와 재확인 문항을 낸다. (1.0은 문자를 항상 50 기준으로 정하고 `boundary` 플래그만 붙인다. 재확인 문항은 없다.)
- 유형 코드 순서는 항상 `[G|S][I|E][N|C][P|O]`. 16개 유형명은 PRD 8.2 표를 정본으로 쓴다(예: GICO = 기술중심 성장형).
- 유형은 우열이 아니다. UI·보고서 문구에서 서열·평가 표현을 쓰지 않는다.

### 4.3 8대 경영역량
- A 전략·사업모델 15, B 시장·고객 15, C 제품·기술 15, D 재무·자금 15, E 조직·창업팀 10, F 생산·운영 10, G 디지털 5, H 성장잠재력 15 (%, 합 100).
- `C_d = Σ(x_i − 1) / (8 × 4) × 100`, `T = Σ W_d · C_d`
- 등급: A ≥85, B ≥70, C ≥55, D ≥40, E <40. (경계값은 하한 포함)
- 가중치는 업종(제조·서비스·도소매)·성장단계별 차등을 전제로 설정 구조를 만든다(값은 미정이므로 기본값 사용).

### 4.4 성장단계 S1~S5
- 6지표(1~5단계) 가중평균: 사업화 20, 고객검증·반복구매 20, 매출추세 20, 수익모델·현금흐름 15, 조직·운영 15, 시장확장·투자 10.
- **필수 통과조건(Gate)이 가중평균보다 우선**한다. 1.0의 시범 Gate(순서대로 적용): S4+ 는 customer≥4·revenue≥4·operations≥3 아니면 S3 / S5 는 operations≥4·expansion≥4 아니면 S4 / S3+ 는 customer≥3·revenue≥2 아니면 S2 / S2+ 는 product≥2 아니면 S1. 잠정단계는 `int(가중지수 + 0.5)`. Gate로 조정되면 사유를 기록한다.
- 업력만으로 단계를 정하지 않는다.

### 4.5 전략추천 (12개 전략군 ST01~ST12)
- `R_j = 0.30F + 0.30U + 0.25E + 0.15X` (각 0~100: 적합성, 시급성, 기대효과, 실행가능성)
- **필수 규칙이 가중점수보다 우선**한다(현금흐름 위험 → 확장투자 보류 등 PRD 8.5의 6개 규칙). 1.0은 이를 `deferred`(보류) 상태와 시급성 가산으로 구현했고, `service_overload`를 더해 플래그가 7종이다. 보류 전략은 목록 뒤로 보내고 사유를 남긴다.
- "점수 낮은 영역 = 추천"이 아니다. 성장목표 달성을 가장 막는 제약을 찾는다.
- 1.0의 실제 계산: U = Σ(100−연계역량)×가중치, F = 40+25×일치목표수, E = 45+20×일치목표수, X = 75 고정(전략별 연계역량·목표대응표는 참고 문서 6절). ⚠ F에 DNA 유형·성장단계가 반영되지 않고 X가 상수다. 12전략 매칭 매트릭스가 나오면 이 부분을 대체한다.
- 결과마다 **추천 근거, 적용된 규칙 ID, 문항·가중치·규칙 버전**을 저장한다(추적 가능성).

### 4.6 회귀 테스트 기준 사례 (엔진 수정 시 항상 통과해야 함)

| 항목 | 그린푸드랩 | 넥스트솔루션 |
| --- | --- | --- |
| DNA | GICO | GINO |
| 단계 | S3 | S4 |
| 종합역량 | 61.87 | 75.16 |
| 추천 1~3 | ST07 재무·자금 → ST06 수익구조 → ST08 조직·인재 | ST08 조직·인재 → ST09 운영체계 → ST03 시장·판로 |

입력값은 1.0의 `create_examples.py`가 목표 점수로부터 만든다(값과 배분 방식은 참고 문서 7절). 이 생성 로직을 그대로 옮겨 테스트 픽스처로 쓴다. 1.0의 자동 테스트 6개(유형·단계·1순위, 누락 오류, 범위 오류, 시장검증 Gate, 현금위험 보류)도 함께 옮긴다. 결측 처리로 바꾸면 "누락 오류" 테스트는 "결측 기록" 테스트로 바꾼다.

## 5. AI 사용 규칙 (FR-20, PRD 9장)

- 점수·유형·단계·전략은 **엔진만** 산출한다. AI는 엔진 결과를 해석·서술하고 실행계획을 구체화만 한다.
- 입력되지 않은 매출·재무 수치를 생성하지 않는다. 불확실한 분석은 별도 표시.
- 사용자 동의가 없거나 API 키가 없으면 규칙기반 보고서만 생성한다(AI 없이도 전 기능 동작).
- AI에는 해석에 필요한 진단결과만 보내고 기업명·연락처 등 식별정보는 보내지 않는다.
- AI 공급자는 미정(시제품은 OpenAI `gpt-4.1-mini`, 정밀형에서만 호출). 공급자 교체가 쉽도록 어댑터 인터페이스 뒤에 둔다. 1.0의 전달 범위(dna·competence·stage·risks·상위 3전략·goals)와 프롬프트 제약을 기준으로 삼는다. 단, 1.0은 `company` 전체를 보내므로 기업명을 빼도록 고친다.

## 6. 보안·데이터 (PRD 10장)

- 접근권한: 기업은 자사만, 컨설턴트는 담당 기업만, 운영기관은 소속 사업의 기업만. **모든 조회 API에 권한 필터를 서버측에서** 적용하고 권한 테스트를 함께 작성한다.
- 재무정보 등 민감 필드는 암호화 저장. 권한·암호화가 갖춰지기 전에는 실제 기업 데이터를 넣지 않는다(테스트는 가상기업만).
- 집계통계는 비식별(소수 집단 노출 방지), 비교는 업종·규모 유사집단 기준.
- 저장·AI 분석 동의 기록을 남긴다.
- 비밀키·API 키는 `.env`에만 두고 커밋하지 않는다. API는 `api/.env`(`bizdna_api/settings.py`가 읽음), 웹은 `web/.env.local`. 커밋하는 것은 `.env.example`뿐이며, 새 환경변수를 추가하면 예시 파일에도 빈 값으로 적는다. 비밀값은 웹 쪽에 두지 않고, 특히 `NEXT_PUBLIC_` 변수는 브라우저에 공개되므로 비밀값에 쓰지 않는다. 운영 배포 시 `BIZDNA_ENV=production`(API 문서 비공개)과 실제 도메인의 `BIZDNA_CORS_ORIGINS`를 설정한다.

## 7. UI·디자인 원칙

- **디자인 기준 문서는 `docs/design-system.md`다.** 비스타컨설팅그룹 홈페이지(https://vistacg.co.kr/, 캡처는 `홈페이지양식/`)의 레이아웃·색·글꼴·컴포넌트·모션을 차용한다. 화면을 만들 때 이 문서의 토큰과 패턴을 먼저 확인한다.
- 핵심 토큰: 글자 `#1d1d1f`, 포인트 파랑 `#0071e3`, 회색 배경 `#f5f5f7`, 보조 글자 `#86868b`, 검정 섹션 `#000`, 서브 히어로 네이비 `#0a1628`, 푸터 `#0f0f11`. 글꼴은 Pretendard, 제목 굵기 800에 좁은 자간, 카드 모서리 30px, 컨테이너 최대 1280px.
- **복제 금지**: VCG 로고·회사명·문구·사진, 그리고 수행기관 로고를 쓰지 않는다(협력 관계가 없는 기관 로고는 오해를 부른다). 실적 수치도 지어내지 않는다. 비스타의 실적 섹션 자리에는 모형 규격(16 유형·8 역량·5 단계·12 전략)을 넣는다.
- PDF 보고서도 웹과 같은 파랑·네이비로 맞춘다. 2.0의 청록 `#0D838B`은 그래프 보조색으로만 쓴다.
- PC·모바일 반응형. 100문항 설문은 영역별 페이지 분할, 진행률 표시, **중간저장** 지원.
- 결과 화면: DNA 4자리 코드와 유형명(MBTI식 카드), 4축 성향 막대(경계 표시 포함), 8대 역량 레이더, 성장단계 진행 바, 핵심 문제, 우선 전략 3개와 근거.
- "가설모형·시범검증 전" 고지를 결과·보고서에 표시한다.

## 8. 개발 우선순위 (PRD 12장)

1. **설계 산출물 먼저**: 100문항 채점기준표, 12전략 매칭 매트릭스가 최우선(없으면 엔진을 완성할 수 없음). 내용이 PRD에 없으면 임의로 만들지 말고 초안임을 표시하거나 사용자에게 확인한다.
2. **MVP = P0(FR-01~FR-12)**: 출시를 막는 것은 FR-01 계정, FR-03 웹 설문, FR-12 저장·권한.
3. P1(컨설턴트 화면, 실행과제, 재진단, 정밀형 보고서, 증빙, 버전관리, 운영기관 화면) → P2(AI 서술, 지원사업 추천, Word 출력 등).

기능을 구현할 때 커밋·PR 설명에 해당 FR ID를 적는다(예: `FR-05 DNA 경계 성향 판정`).

## 9. 미결정 사항 (PRD 13장 — 결정되면 여기에 기록)

- [ ] 대상 범위: 중소기업 전체 vs 창업·성장기업 중심
- [ ] 1차 업종: 제조·서비스·도소매 전부 vs 제조업 우선
- [ ] 수익모델: 기본형 무료·정밀형 유료 vs 기관 판매
- [x] 화면 기술: Next.js 16 + FastAPI (2026-11-16)
- [x] DB·인증: Supabase (PostgreSQL + Supabase Auth), 배포: Vercel (2026-11-16)
- [ ] 로그인 방식: 이메일+비밀번호만 vs 카카오·네이버·구글 소셜 로그인 추가 (11.3)
- [ ] 비로그인 체험 허용 범위: 기본진단까지 비로그인 허용 vs 처음부터 가입 필수 (11.3)
- [ ] 컨설턴트·운영기관 계정 발급 방식: 관리자 초대만 vs 신청 후 승인 (11.3)
- [ ] 민감 재무 필드의 추가 암호화(컬럼 단위) 여부 (11.4)
- [ ] AI 공급자와 전달 데이터 범위
- [ ] 시범검증 표본·협력기관
- [ ] 성공지표·성능 목표치
- [ ] 서비스명 (Biz-DNA는 가칭 — 코드에서는 설정값으로 관리)

이 항목에 영향을 받는 작업은 임의로 확정하지 말고 가정을 명시하거나 사용자에게 묻는다.

## 10. 작업 규칙

- 엔진 로직 변경 → `api/engine/tests` 전체와 회귀 사례 통과 확인 후 완료 보고.
- 가중치·임계값·문항 변경 → 설정 파일 버전을 올리고, 기존 진단 회차는 당시 버전으로 재현 가능해야 한다.
- 결측·경계값(40, 60, 등급 경계) 처리에 단위 테스트를 반드시 둔다.
- 사용자 대면 문구는 "창업자" 대신 상황에 따라 "경영자"를 검토한다(성숙 기업 적합성 리스크).
- 컨설팅 효과를 인과적으로 주장하는 문구를 쓰지 않는다.

## 11. DB·회원가입·로그인·배포 (Supabase + Vercel)

2026-11-16 결정: DB와 인증은 **Supabase**, 배포는 **Vercel**. 아직 구현 전이며, 아래는 구현할 때 따를 설계다. Supabase·Vercel·Next.js 16의 API는 자주 바뀌므로 코드를 쓰기 전에 공식 문서(또는 설치된 패키지의 문서)를 다시 확인한다.

### 11.1 전체 구조

```
브라우저 ──(로그인·세션)──▶ Supabase Auth
   │
   ▼  Vercel 프로젝트 1개 (Vercel Services)
 web 서비스 (Next.js)          api 서비스 (FastAPI, Python 3.12)
   │  /api/* 요청에 Supabase access token을          │
   │  Authorization: Bearer 로 실어 보냄 ──────────▶ │ JWT 검증 → 권한 확인 → 엔진 실행
   │                                                  ▼
   │                                        Supabase Postgres (진단·기업 데이터)
```

- **역할 분담**: 브라우저는 Supabase를 **로그인에만** 쓴다. 기업·진단 데이터의 읽기·쓰기는 모두 FastAPI를 거친다. 권한 검사(6장)와 엔진 실행을 한곳에 모으기 위해서다. 브라우저에서 Supabase 테이블을 직접 조회하는 기능은 만들지 않는다.
- **엔진 위치**: 진단엔진(`api/engine/`)은 그대로 API 안에서 실행한다. DB에 들어가는 것은 응답과 결과뿐이다.

### 11.2 Supabase 설정

- **연결**: Vercel Marketplace의 Supabase 연동(Vercel Native)으로 프로젝트를 만든다. 그러면 Vercel 환경변수가 자동 등록된다.
  - 공개 가능: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (웹 브라우저용)
  - 서버 전용: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `POSTGRES_URL`(풀링), `POSTGRES_URL_NON_POOLING`, `POSTGRES_USER`·`POSTGRES_PASSWORD`·`POSTGRES_HOST`·`POSTGRES_DATABASE`
  - 로컬에서는 `vercel env pull`로 받는다. **`SUPABASE_SECRET_KEY`와 `POSTGRES_*`는 api 쪽에서만 쓴다.** web 코드나 `NEXT_PUBLIC_` 변수에 넣지 않는다.
  - 연동되면 `api/.env.example`의 임시 자리(`DATABASE_URL`, `BIZDNA_AUTH_SECRET`)를 위 이름으로 바꾼다. Supabase JWT를 쓰므로 자체 서명 키는 필요 없다.
- **리전**: 한국 기업 데이터이므로 Supabase는 서울(ap-northeast-2)을 쓰고, Vercel 함수 리전도 서울(icn1)로 맞춘다.
- **마이그레이션**: 스키마·RLS 정책·트리거는 `supabase/migrations/*.sql`에 SQL로 남긴다(Supabase CLI). 대시보드에서 손으로 바꾼 내용은 반드시 마이그레이션 파일로 옮긴다. Alembic은 쓰지 않는다.
- **RLS 필수**: `public` 스키마의 테이블은 공개 키(publishable key)로 Data API를 통해 접근될 수 있다. 그래서 **모든 테이블에 RLS를 켠다.** 정책 없이 RLS만 켜 두면 브라우저의 직접 접근이 막히고, FastAPI는 서버 전용 DB 연결로 접근한다. 정책은 "본인 기업만 조회"처럼 6장 권한과 같은 규칙을 이중 방어로 추가한다.
- **API의 DB 연결**: FastAPI는 `POSTGRES_URL`(풀링 연결)을 쓴다. 서버리스 환경이므로 연결을 짧게 쓰고, 트랜잭션 풀러를 쓸 때는 prepared statement를 끈다.
- **파일**: 증빙자료(FR-17)와 보관용 PDF는 Supabase Storage의 **비공개 버킷**에 두고, 내려받을 때는 API가 짧은 유효기간의 서명 URL을 발급한다. 지금처럼 PDF를 요청할 때마다 만들면 저장하지 않아도 된다.

### 11.3 회원가입·로그인 (FR-01)

- **웹 (Next.js 16)**: `@supabase/ssr`를 쓴다. 브라우저 컴포넌트는 `createBrowserClient`, 서버 컴포넌트·서버 액션·라우트 핸들러는 `createServerClient`를 쓴다.
  - **`web/proxy.ts`가 필요하다**(Next 16에서 middleware의 새 이름). 여기서 `supabase.auth.getClaims()`를 호출해 만료된 세션을 갱신하고 쿠키에 다시 쓴다.
  - 서버에서 사용자를 확인할 때는 **`getClaims()`**를 쓴다. 서버 코드에서 `getSession()` 결과를 믿지 않는다(쿠키를 검증 없이 읽기 때문).
- **API (FastAPI)**: `Authorization: Bearer <access token>`을 받아 Supabase 공개 서명 키(`{SUPABASE_URL}/auth/v1/.well-known/jwks.json`)로 검증한다. 키는 메모리에 캐시하되, 모르는 `kid`가 오면 다시 받는다. 검증한 `sub`가 사용자 ID다.
- **역할 저장 위치**: 역할(기업·컨설턴트·운영기관·관리자)은 **사용자가 수정할 수 없는 곳**에 둔다. 즉 DB의 `memberships` 테이블이나 Auth의 `app_metadata`에 둔다. `user_metadata`는 사용자가 직접 바꿀 수 있으므로 권한 판단에 쓰지 않는다. 권한은 매 요청마다 DB 기준으로 확인한다.
- **가입 흐름 (기업 담당자)**:
  1. 이메일·비밀번호로 가입하고 이메일 인증을 거친다.
  2. 개인정보 수집·이용 동의와 진단결과 저장 동의를 받는다(`consents`). AI 분석 동의는 따로 받는다.
  3. 기업을 등록하고(FR-02 기업정보), 가입한 사람이 그 기업의 `owner`가 된다.
  4. 진단을 시작한다. 로그인 전에 브라우저에 저장된 응답(`bizdna.survey.v1`)이 있으면 "이 응답을 내 계정으로 가져오기"를 제안한다.
- **컨설턴트·운영기관·관리자**: 스스로 가입하지 않는다. 관리자가 초대하거나 승인해 역할을 부여한다(9장 미결정 항목).
- **결정 전까지의 기본값**: 이메일+비밀번호 로그인. 비로그인으로도 기본진단과 결과 보기는 가능하고, 결과 저장·정밀진단·PDF·재진단은 로그인 후에 쓸 수 있다. 소셜 로그인과 비로그인 범위는 9장에서 확정한다.
- **Auth 설정**: Supabase 대시보드의 Site URL과 Redirect URL에 운영 도메인, `http://localhost:3000`, Vercel 미리보기 주소를 등록한다. Vercel 연동은 미리보기 브랜치의 리다이렉트 URL을 자동으로 만든다. 이메일 발송은 운영 전에 별도 SMTP를 연결한다(기본 발송은 한도가 낮다).
- **탈퇴·삭제**: 회원 탈퇴 시 개인정보를 삭제한다. 기업 진단 데이터의 보관 기간과 비식별 처리는 개인정보처리방침에 정하고 그대로 구현한다.

### 11.4 데이터 모델 (PRD 11장 "저장할 데이터" 기준, 초안)

| 테이블 | 핵심 컬럼 | 비고 |
| --- | --- | --- |
| `profiles` | `id`(= auth.users.id), 이름, 연락처, 가입일 | 가입 시 트리거로 생성 |
| `organizations` | 이름, 유형(운영기관·컨설팅사) | |
| `memberships` | `user_id`, `role`(company·consultant·agency·admin), `organization_id` | 역할의 정본 |
| `companies` | 기업정보(FR-02): 업종, 설립연도, 매출, 영업이익률, 인력, 고객·채널, 목표, 투자계획 | 민감 정보 |
| `company_members` | `company_id`, `user_id`, `role`(owner·member) | 기업 담당자 ↔ 기업 |
| `consultant_assignments` | `consultant_id`, `company_id`, 기간 | 컨설턴트는 담당 기업만 조회 |
| `program_enrollments` | `organization_id`(운영기관), `company_id`, 사업명 | 운영기관은 소속 사업 기업만 조회 |
| `diagnoses` | `company_id`, `phase`(basic·full), `status`, `survey`(jsonb), `result`(jsonb), `model_version`, `questions_version`, `created_by`, 생성·완료 시각 | 진단 회차. 결과와 버전을 함께 저장해 재현 가능하게 한다 |
| `consents` | `user_id`, `company_id`, 종류(개인정보·결과저장·AI), 약관 버전, 동의 시각, 철회 시각 | |
| `audit_logs` | 누가·언제·무엇을 조회·수정했는지 | 민감 데이터 접근 기록 |
| (P1) `action_items`, `kpi_records`, `evidence_files` | 90일 실행과제, KPI 실적, 증빙 | |

- 문항과 가중치의 정본은 지금처럼 `api/engine/bizdna/config/*.json`이다. 관리자 화면에서 바꾸는 기능(FR-18)이 생길 때 DB로 옮길지 정한다.
- 암호화: Supabase는 저장 데이터와 전송 구간을 기본으로 암호화한다. 매출·영업이익률 같은 필드를 컬럼 단위로 추가 암호화할지는 9장 미결정 항목이다.

### 11.5 Vercel 배포

- **구성**: 저장소 루트에 Vercel Services 설정을 두고 `web`(Next.js)과 `api`(FastAPI) 두 서비스를 한 프로젝트로 배포한다. 두 서비스는 항상 함께 배포·롤백된다.
  - 공개 라우팅: `/api/(.*)` → api 서비스, 그 외 `/(.*)` → web 서비스. 현재 Next.js에는 자체 API 라우트가 없으므로 api가 `/api` 전체를 맡는다. api는 원래 경로(`/api/...`)를 그대로 받는데, FastAPI 라우트가 이미 `/api`로 시작하므로 경로를 바꿀 필요가 없다.
  - 웹과 API가 같은 도메인이 되므로 운영에서는 CORS가 필요 없다. `next.config.ts`의 `/api` rewrites와 `BIZDNA_API_URL`은 로컬 개발용으로만 남긴다.
  - 설정 파일은 `vercel.json`의 `services` 또는 권장 방식인 `vercel.ts`(`@vercel/config`)로 작성한다. 작성 전에 최신 문서를 확인한다.
- **배포 상태 (2026-11-16)**: Vercel 프로젝트 `21111/mbti-for-enterprise`(프레임워크 프리셋 `services`, Root Directory는 저장소 루트)에 배포했다. 설정은 루트 `vercel.json`이다. 처음 계획한 배포 전 문제 3가지는 다음처럼 해결했다.
  1. **엔진 import 경로**: `engine/`을 `api/engine/`으로 옮겨 api 서비스 묶음 안에 넣었다. `api/bizdna_api/main.py`가 `sys.path`로 불러온다.
  2. **PDF 한글 폰트**: 나눔고딕(OFL, `api/fonts/`)을 저장소에 넣고 기본 폰트로 쓴다. 환경변수 `BIZDNA_FONT_*`로 바꿀 수 있다.
  3. **런타임 버전**: Python 3.12(`api/.python-version`), Node는 `web/package.json`의 `engines`가 22 이상이며 프로젝트 설정은 26.x다.
- **배포에 올리지 않는 파일**: `.vercelignore`(CLI 배포 시 legacy·prototype·docs·캡처·로컬 비밀값 제외). 운영 의존성은 `api/requirements.txt`, 테스트 도구는 `api/requirements-dev.txt`에 둔다.
- **배포 확인 방법**: 미리보기는 Vercel 인증으로 보호되므로 `vercel curl <경로> --deployment <URL>`로 확인한다. Git Bash에서는 `MSYS_NO_PATHCONV=1`을 붙여야 `/api/...` 경로가 Windows 경로로 바뀌지 않는다.
- **Vercel CLI 주의**: 환경변수 삭제(`vercel env rm`)는 사람의 승인이 필요하다. 값만 바꿀 때는 `vercel env update <NAME> --environment production --value ... --yes`를 쓴다. `vercel link`는 루트에 `.env.local`(OIDC 토큰)을 만들고 `.gitignore`에 `.env*`를 덧붙이는데, 그 줄은 `.env.example`까지 막으므로 지운다.
- **환경변수**: Vercel 대시보드에 Production·Preview·Development 별로 등록한다. Supabase 연동 변수는 자동 등록되고, 그 외에 `BIZDNA_ENV=production`, 폰트 경로, (향후) AI 키를 등록한다. 미리보기 배포가 운영 DB를 건드리지 않도록 Preview에는 별도 Supabase 프로젝트나 브랜치를 연결한다.
- **제한**: 함수 요청·응답 본문은 최대 4.5MB다(현재 PDF는 약 0.15MB). 함수 기본 실행시간 제한은 300초다.
- **미리보기 보호**: 미리보기 배포는 Vercel Deployment Protection으로 팀원만 보게 한다.
- **로컬 개발**: 지금처럼 `run_dev.bat`을 쓰거나, Services 설정 후에는 `vercel dev`로 두 서비스를 함께 띄운다.

### 11.6 구현 순서 (권장)

1. Vercel 프로젝트 연결, Supabase 연동 설치, `vercel env pull` → `.env.example` 변수명 정리
2. `supabase/migrations`에 11.4 테이블과 RLS 작성
3. 웹: `@supabase/ssr` 클라이언트, `proxy.ts`, 가입·로그인·로그아웃·비밀번호 재설정 화면(디자인은 `docs/design-system.md`의 서브페이지 패턴)
4. API: JWT 검증 의존성, 권한 검사, `/api/companies`·`/api/diagnoses` 저장·조회. 권한 테스트(타 기업 조회 차단 등)를 함께 작성한다
5. 설문·결과 화면을 localStorage 저장에서 서버 저장으로 바꾸고, 비로그인 응답 가져오기를 넣는다
6. 11.5의 배포 전 문제 3가지를 해결하고 미리보기 배포로 전체 흐름 확인 → 운영 배포
