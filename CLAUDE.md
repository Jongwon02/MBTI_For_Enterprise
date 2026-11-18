# CLAUDE.md

이 파일은 Claude Code가 이 저장소에서 작업할 때 따라야 할 지침이다. 상세 요구사항의 원천은 `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md`(이하 PRD)이며, 이 문서와 PRD가 충돌하면 PRD가 우선한다. PRD를 바꾸는 결정이 생기면 PRD와 이 파일의 "결정 사항" 절을 함께 갱신한다.

## 1. 프로젝트 개요

- **서비스**: Biz-DNA(가칭). 중소기업(창업·성장기업 포함)이 온라인 진단 100문항에 답하면 **DNA 유형(16종, MBTI식 4자리 코드) · 성장단계(S1~S5) · 8대 경영역량 점수 · 우선 전략 3개 · PDF 보고서**를 받는 경영진단 웹사이트.
- **흐름**: 기업정보 입력 → 기본진단 → 정밀진단 → 결과 대시보드 → 보고서 → 90일 실행 → 3·6·12개월 재진단.
- **사용자 역할 4종**: 기업 담당자(주 사용자), 컨설턴트, 운영기관, 시스템 관리자.
- **범위 밖(구현 금지)**: 소상공인(점포) 진단, 상권·카드매출 분석, 지원사업 신청자격 판정, 외부 재무데이터 자동 연계, AI의 점수·유형 직접 산출.
- **문서 언어**: UI 문구, 주석, 커밋 메시지, 문서는 한국어. 코드 식별자(변수·함수·테이블명)는 영어.

## 2. 현재 상태 (2026-11-18)

**진단 기능이 실제로 동작한다**: 기업정보 → 기본진단(DNA 24·성장단계 6·목표/장애) → 기본 결과 → 정밀진단(역량 64·성장계획) → 결과 대시보드 → PDF(기본형·정밀형).

| 구분 | 상태 |
| --- | --- |
| 구현됨 | FR-02 기업정보, FR-03 웹 설문(기본/정밀 구분, 중간저장), FR-04 완결성 검증·결측 처리, FR-05~09 엔진, FR-10 결과 대시보드, FR-11 기본형 PDF, FR-13 정밀형 PDF(약 10쪽, 15~20쪽 목표 미달) |
| 구현됨 (2026-11-17·18) | FR-01 **아이디+비밀번호** 회원가입·로그인·로그아웃(Supabase Auth, 이메일 인증 없음), 게스트 진단, 마이페이지(중간저장 이어하기·최종저장 결과 보기·삭제), FR-12 회원 진단 회차 서버 저장(본인 회차만 접근) |
| 구현됨 (2026-11-18) | 경영자 성향 데이터 수집(12장: `analytics`·`private` 스키마, 최종저장 시 같은 트랜잭션에서 수집, 백필), 관리자 계정(`memberships`의 admin)과 관리자 화면 `/admin`(집계·회차 목록·상세·CSV, 15초 자동 갱신, 감사 기록). 사용법은 `docs/admin.md` |
| 없음 | 역할 중 컨설턴트·운영기관(관리자만 있음), `companies` 테이블, 비밀번호 재설정, 회원 탈퇴, 소셜 로그인, 업종별 문항 분기, FR-14 이후 전부, AI 서술(FR-20) |
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
| 차트 | Recharts (역량 레이더, 관리자 분포 막대) | 사용 중 |
| PDF | ReportLab (2.0 방식). 폰트: `BIZDNA_FONT_REGULAR/BOLD` → 맑은 고딕 → 나눔 순으로 찾음 | 사용 중 |
| DB | **Supabase** (PostgreSQL, 마이그레이션은 `supabase/migrations/*.sql`, 적용은 `scripts/migrate.py`) | 사용 중 (11장) |
| 회원가입·로그인 | **Supabase Auth** (웹: `@supabase/ssr`, API: PyJWT로 JWT 검증) | 사용 중 (11장) |
| 배포 | **Vercel** (한 프로젝트에 web + api 서비스) | 결정됨 · 미구현 (11장) |
| 테스트 | pytest (엔진·API) | 화면 테스트(Playwright)는 없음 |

**Next.js 16은 학습 데이터와 다르다.** 코드를 쓰기 전에 `web/node_modules/next/dist/docs/`의 해당 문서를 확인한다(`web/AGENTS.md`). 브라우저 저장소를 읽는 화면은 `next/dynamic`의 `ssr: false` 래퍼(`SurveyClient`, `ResultClient`)로 감싸 effect 안 setState를 피한다(eslint `react-hooks/set-state-in-effect`).

### 디렉터리 구조

```
api/engine/bizdna/  engine.py(진단·전략), survey.py(설문→엔진 입력, 완결성), config.py
  config/           model_v1.json(가중치·임계값·규칙), questions_v1.json(문항·초안 문항)
api/engine/tests/   fixtures.py(기준 사례), test_regression.py(legacy 대조), test_engine.py
api/bizdna_api/     main.py(/api/questions, /api/diagnose, /api/completeness, /api/report, /api/me, /api/diagnoses),
                    auth.py(JWT 검증), signup.py(가입: 관리자 API), store.py(진단 회차 저장소: Postgres·테스트용 Memory, 수집·관리자 조회),
                    analytics.py(12장 방향값·derive_rows·집계, 순수 함수), admin.py(/api/admin/*), report.py(PDF)
api/tests/          test_api.py, test_diagnoses.py(토큰·권한), test_signup.py, test_analytics.py, test_admin.py
supabase/migrations/ 스키마·RLS·가입 트리거·분석 저장소 SQL
scripts/            migrate.py(마이그레이션 적용), grant_admin.py(관리자 계정), backfill_analytics.py(분석 저장소 백필), seed_dummy.py(더미 진단 생성·삭제)
web/app/            page.tsx(메인), diagnosis/(설문·결과), login/, signup/, mypage/, admin/, styles/*.css
web/proxy.ts        Supabase 세션 갱신, 비로그인 /mypage·/admin 접근 시 /login으로
web/components/     SiteHeader(우측 상단 관리자·로그인·마이페이지)·SiteFooter, home/, auth/(LoginForm, SignupForm),
                    survey/(DiagnosisEntry: 로그인·가입·게스트 선택, SurveyApp, fields), result/, mypage/, admin/(AdminApp, charts, FactDetail)
web/lib/            api.ts, auth.ts(useAuth·토큰), useIsAdmin.ts, admin-types.ts, supabase/(config·client), storage.ts(localStorage), types.ts, sample.ts, content.ts
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
- [x] 로그인 방식: **아이디 + 비밀번호만, 이메일 인증 없음** (2026-11-17 이메일 인증 안 함, 2026-11-18 이메일 대신 아이디로 결정). 이메일은 받지 않는다. 소셜 로그인은 추가하지 않는다(다시 요청이 있을 때 검토)
- [x] 비로그인 체험 허용 범위: **게스트는 전체 진단(기본·정밀·PDF) 허용**, 응답은 브라우저에만 저장하고 마이페이지는 없음 (2026-11-17)
- [ ] 컨설턴트·운영기관 계정 발급 방식: 관리자 초대만 vs 신청 후 승인 (11.3)
- [ ] 민감 재무 필드의 추가 암호화(컬럼 단위) 여부 (11.4)
- [ ] AI 공급자와 전달 데이터 범위
- [ ] 시범검증 표본·협력기관
- [ ] 성공지표·성능 목표치
- [ ] 서비스명 (Biz-DNA는 가칭 — 코드에서는 설정값으로 관리)
- [ ] 경영자 성향 데이터 수집(분석 저장소)의 동의·삭제 처리·재무 원값 암호화·집계 구간 (12.10). 수집 방식은 2026-11-18 확정(12.2), 리전은 뭄바이 유지(2026-11-18)

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
- **연결 상태 (2026-11-18)**: Vercel Marketplace 연동이 아니라 사용자가 직접 만든 Supabase 프로젝트 `MBTI`(ref `jjjgyzmdqnskxussdhte`)를 수동 연결했다. 리전은 **뭄바이(ap-south-1)**로 위 권장(서울)과 다르지만, **옮기지 않기로 했다**(2026-11-18 사용자 결정: 이전 작업 부담 대비 이득이 작음). 리전 이전을 다시 제안하지 않는다. DB 접속은 풀러 `aws-0-ap-south-1.pooler.supabase.com`(6543 = `POSTGRES_URL`, 5432 = `POSTGRES_URL_NON_POOLING`). 마이그레이션 `20261117000000`은 `scripts/migrate.py`로 적용했다. Vercel 환경변수 6개(`SUPABASE_URL`·`SUPABASE_SECRET_KEY`·`POSTGRES_URL`·`POSTGRES_URL_NON_POOLING`·`NEXT_PUBLIC_SUPABASE_URL`·`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`)는 **Production에만** 등록했다. 프로젝트가 하나뿐이어서, 미리보기는 회원 기능 없이 게스트 진단만 된다. 로컬 `api/.env`에는 원본 값 `SUPABASE_DB_PASSWORD`도 있다(git 제외).
- **Auth 설정 주의**: Sign In / Providers의 **Email provider는 켜고 Confirm email만 끈다.** 아이디 로그인도 내부적으로는 Email provider(내부용 주소)를 쓰기 때문이다. Email provider를 끄면 가입(관리자 API)은 되지만 로그인이 `email_provider_disabled`(422)로 막힌다(2026-11-18 운영에서 확인).
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
  1. **아이디·비밀번호로 가입한다. 이메일은 받지 않고 이메일 인증도 없다**(2026-11-18 결정).
  2. 개인정보 수집·이용 동의와 진단결과 저장 동의를 받는다(`consents`). AI 분석 동의는 따로 받는다.
  3. 기업을 등록하고(FR-02 기업정보), 가입한 사람이 그 기업의 `owner`가 된다.
  4. 진단을 시작한다. 로그인 전에 브라우저에 저장된 응답(`bizdna.survey.v1`)이 있으면 "이 응답을 내 계정으로 가져오기"를 제안한다.
- **컨설턴트·운영기관·관리자**: 스스로 가입하지 않는다. 관리자가 초대하거나 승인해 역할을 부여한다(9장 미결정 항목). **관리자**는 `scripts/grant_admin.py`로 만들거나 권한을 준다(`docs/admin.md`). 첫 관리자 아이디는 `whoami`(2026-11-18).
- **아이디 로그인 (2026-11-18 결정, 반드시 지킬 것)**: 가입·로그인은 **아이디 + 비밀번호만** 쓴다. **이메일 입력·이메일 인증·인증 메일 발송·이메일 기반 비밀번호 재설정을 만들지 않는다.** Supabase Auth는 이메일로만 계정을 만들 수 있으므로 아이디를 내부용 주소 `{아이디}@users.bizdna.invalid`로 바꿔 쓴다(`.invalid`는 메일이 가지 않는 예약 도메인). 이 주소는 화면에 보여주지 않고 아이디만 보여준다(`loginId`). 아이디 규칙은 영문 소문자로 시작하는 영문 소문자·숫자·밑줄 4~20자이고, 입력은 소문자로 바꾼다. 규칙과 도메인은 `api/bizdna_api/signup.py`(`USERNAME_RE`, `LOGIN_DOMAIN`)와 `web/lib/auth.ts`(`USERNAME_RE`, `usernameToEmail`) 두 곳에 있으므로 함께 고친다. 아이디는 `user_metadata.username`에도 넣지만 표시용이며 권한 판단에 쓰지 않는다. 비밀번호를 잊은 경우의 재설정은 메일 없이 할 방법(관리자 재설정 등)을 따로 정해야 한다(미구현).
- **현재 동작 (2026-11-18)**: 아이디+비밀번호 가입·로그인, **이메일 인증 없음**(사용자 결정). 가입은 브라우저가 아니라 `POST /api/auth/signup`이 Supabase 관리자 API(`SUPABASE_SECRET_KEY`)로 `email_confirm: true` 계정을 만들고, 화면이 바로 `signInWithPassword`로 로그인한다. 그래서 대시보드의 "Confirm email" 설정과 무관하다. 가입 API에는 아직 요청 횟수 제한이 없다(운영 전 Vercel Firewall 등으로 추가 검토). `/diagnosis`에 들어오면 로그인·회원가입·게스트 중 하나를 고른다. 게스트는 전체 진단을 할 수 있지만 응답은 브라우저에만 남는다. 회원은 단계를 넘길 때와 "중간저장" 때 서버에 `draft`로, 기본진단·정밀진단을 마치면 서버가 엔진을 돌려 결과와 버전을 함께 저장한다(`basic_completed`·`full_completed`, 상태는 낮아지지 않음). 마이페이지는 진행 중 회차(이어하기)와 완료 회차(저장 당시 결과 보기, 정밀진단 이어하기, 삭제)를 보여준다. 로그아웃하면 브라우저에 남은 회원 응답을 지운다. 소셜 로그인은 하지 않는다(9장).
- **동의**: 가입 화면의 필수 동의 3종(개인정보, 결과저장, **통계 활용**(2026-11-18 추가, 12.2))은 `user_metadata.consents`로 보내고 가입 트리거가 `consents` 테이블로 옮긴다. 문구는 초안(`TERMS_VERSION = 2026-11-18-draft`)이다. 2026-11-18 이전 가입자에게는 통계 활용 동의가 없어 수집되지 않는다. AI 동의는 AI 기능을 만들 때 추가한다.
- **Auth 설정**: Supabase 대시보드의 Site URL과 Redirect URL에 운영 도메인, `http://localhost:3000`, Vercel 미리보기 주소를 등록한다. Vercel 연동은 미리보기 브랜치의 리다이렉트 URL을 자동으로 만든다. 아이디 로그인이라 메일을 보내지 않으므로 SMTP는 필요 없다.
- **탈퇴·삭제**: 회원 탈퇴 시 개인정보를 삭제한다. 기업 진단 데이터의 보관 기간과 비식별 처리는 개인정보처리방침에 정하고 그대로 구현한다.

### 11.4 데이터 모델 (PRD 11장 "저장할 데이터" 기준, 초안)

| 테이블 | 핵심 컬럼 | 비고 |
| --- | --- | --- |
| `profiles` | `id`(= auth.users.id), 이름, 연락처, 가입일 | 가입 시 트리거로 생성 |
| `organizations` | 이름, 유형(운영기관·컨설팅사) | |
| `memberships` | `user_id`, `role`(company·consultant·agency·admin), `organization_id` | 역할의 정본. **구현됨(2026-11-18)**: 지금은 `admin`만 쓴다 |
| `companies` | 기업정보(FR-02): 업종, 설립연도, 매출, 영업이익률, 인력, 고객·채널, 목표, 투자계획 | 민감 정보 |
| `company_members` | `company_id`, `user_id`, `role`(owner·member) | 기업 담당자 ↔ 기업 |
| `consultant_assignments` | `consultant_id`, `company_id`, 기간 | 컨설턴트는 담당 기업만 조회 |
| `program_enrollments` | `organization_id`(운영기관), `company_id`, 사업명 | 운영기관은 소속 사업 기업만 조회 |
| `diagnoses` | `company_id`, `phase`(basic·full), `status`(draft·basic_completed·full_completed), `survey`·`progress`·`result`(jsonb), `model_version`, `questions_version`, `created_by`, 생성·완료 시각 | 진단 회차. 결과와 버전을 함께 저장해 재현 가능하게 한다. **구현됨**: `companies`가 생기기 전까지 권한은 `created_by` 기준, `company_id`는 비어 있음 |
| `consents` | `user_id`, `company_id`, 종류(개인정보·결과저장·AI·통계 활용), 약관 버전, 동의 시각, 철회 시각 | **구현됨** |
| `audit_logs` | 누가·언제·무엇을 조회·수정했는지 | 민감 데이터 접근 기록. **구현됨(2026-11-18)**: `private.audit_logs`, 지금은 관리자 조회·내보내기만 기록 |
| `analytics.*`, `private.subject_map` | 경영자 성향 데이터 수집 | 12장. **구현됨(2026-11-18)** |
| (P1) `action_items`, `kpi_records`, `evidence_files` | 90일 실행과제, KPI 실적, 증빙 | |

- 문항과 가중치의 정본은 지금처럼 `api/engine/bizdna/config/*.json`이다. 관리자 화면에서 바꾸는 기능(FR-18)이 생길 때 DB로 옮길지 정한다.
- 암호화: Supabase는 저장 데이터와 전송 구간을 기본으로 암호화한다. 매출·영업이익률 같은 필드를 컬럼 단위로 추가 암호화할지는 9장 미결정 항목이다.

### 11.5 Vercel 배포

- **구성**: 저장소 루트에 Vercel Services 설정을 두고 `web`(Next.js)과 `api`(FastAPI) 두 서비스를 한 프로젝트로 배포한다. 두 서비스는 항상 함께 배포·롤백된다.
  - 공개 라우팅: `/api/(.*)` → api 서비스, 그 외 `/(.*)` → web 서비스. 현재 Next.js에는 자체 API 라우트가 없으므로 api가 `/api` 전체를 맡는다. api는 원래 경로(`/api/...`)를 그대로 받는데, FastAPI 라우트가 이미 `/api`로 시작하므로 경로를 바꿀 필요가 없다.
  - 웹과 API가 같은 도메인이 되므로 운영에서는 CORS가 필요 없다. `next.config.ts`의 `/api` rewrites와 `BIZDNA_API_URL`은 로컬 개발용으로만 남긴다.
  - 설정 파일은 `vercel.json`의 `services` 또는 권장 방식인 `vercel.ts`(`@vercel/config`)로 작성한다. 작성 전에 최신 문서를 확인한다.
- **배포 상태 (2026-11-16)**: 운영 주소 **https://mbti-for-enterprise-21111.vercel.app** (누구나 접속 가능). Vercel 프로젝트 `21111/mbti-for-enterprise`(프레임워크 프리셋 `services`, Root Directory는 저장소 루트)이며, GitHub `main`에 푸시하면 운영에 자동 배포된다. 배포 보호는 `prod_deployment_urls_and_all_previews`((Legacy) Standard Protection)로, 최신 운영 주소만 공개하고 미리보기·개별 배포 주소는 Vercel 팀원만 볼 수 있다. 사용자 도메인을 연결하면 Standard Protection으로 바꿔도 된다. 설정은 루트 `vercel.json`이다. 처음 계획한 배포 전 문제 3가지는 다음처럼 해결했다.
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

## 12. 경영자 성향 데이터 수집 (진단 데이터 분석 저장소) (2026-11-18 구현됨)

> **2026-11-18 구현·운영 DB 적용 완료.** 마이그레이션 `supabase/migrations/20261118000000_analytics_admin.sql`, 코드 `api/bizdna_api/analytics.py`·`store.py`·`admin.py`, 백필 `scripts/backfill_analytics.py`. 관리자 화면·계정은 `docs/admin.md`. 설계와 다르게 구현한 점은 12.13에 적었다.

### 12.1 목적

회원들의 진단을 모아 "의미 있는 정보"로 바꾼다.

| 쓰임 | 예 | 근거 |
| --- | --- | --- |
| 유사집단 비교·집계 | 업종·규모·업력·단계별 DNA 방향 분포, 역량 점수 분위, 성장장애·목표·정책수요 분포 | FR-19, PRD 10장 "유사집단 비교·비식별 집계" |
| 변화 추적 | 재진단 때 유형·방향·단계·점수 변화, 유형 안정성(검사-재검사), 진단 완료율·정밀진단 전환율·재진단율 | FR-16, PRD 3장 사용 지표 |
| 모형 검증 (일부) | DNA 경계 비율, 성장단계 Gate 적용 빈도, 전략 추천·보류 빈도, 가중치 재조정 근거 | PRD 3장 검증 지표 |

문항 단위 신뢰도(Cronbach's α, 문항 변별도)는 문항 응답을 저장하지 않기로 했으므로(12.2) 이 저장소만으로는 계산할 수 없다. 필요해지면 12.9의 방법으로 추가한다.

### 12.2 결정 사항 (2026-11-18, 사용자 확정)

| 항목 | 결정 |
| --- | --- |
| 수집 함수 | `derive_rows(diagnosis, *, subject_key, round_no)` **순수 함수**. 가명키와 회차 번호는 DB를 아는 호출자가 구해서 넘긴다. DB·HTTP에 의존하지 않는다(엔진과 같은 방식) |
| 회차 단위 | 한 진단 회차는 **최종 상태 1행**. 기본진단 완료 후 같은 회차로 정밀진단을 마치면 기본진단 행을 덮어쓴다. 고유키 `(diagnosis_id, model_version)`. 기본진단에서 멈춘 사람은 `funnel_events`로 센다 |
| 경영자 성향(DNA) | 24문항 응답을 저장하지 않고 **4축 방향값**만 저장한다(12.4 알고리즘). 방향값에서 축 점수·유형 문자·경계 여부를 역산할 수 있다 |
| 그 밖의 값 | **구간화하지 않고 원값 그대로** 저장한다(설립연도, 매출, 전년 매출, 영업이익률, 인력, 성장단계 6지표, P문항 원값, 엔진 점수). 구간은 집계·표시 단계(12.8)에서만 쓴다 |
| 역량 | 64문항 응답은 저장하지 않고 엔진이 낸 8영역 점수·종합점수·등급을 저장한다. 역량은 "방향"이 아니라 "수준"이므로 0~100 점수 그대로 둔다 |
| 문항 단위 응답 | 분석 저장소에 저장하지 않는다. 원본은 `public.diagnoses.survey`에 남으므로 나중에 백필로 추가할 수 있다(12.9) |
| 식별정보 | 화이트리스트(12.5)에 있는 값만 꺼낸다. 기업명·자유서술·회원 ID는 넣지 않는다 |
| 통계 활용 동의 | **가입 필수 동의에 포함**한다(2026-11-18 사용자 결정). 가입 화면에 [필수] 통계 활용 동의를 추가했다 |
| 삭제 | **회원이 회차를 지우거나 계정을 삭제해도 분석 행은 남긴다**(2026-11-18 사용자 결정). 탈퇴 시 `private.subject_map`만 지워져 가명 상태가 된다 |
| 관리자 화면 | **집계 + 개별 회차 목록·상세**를 화면에서 본다(2026-11-18 사용자 결정). 기업명·아이디는 보이지 않고 조회는 감사 기록에 남는다 |

### 12.3 원칙

1. **원본과 분석용을 나눈다.** `public.diagnoses`는 서비스용 원본이자 정본이다. 분석 행은 여기서 **파생**하므로 언제든 지우고 백필로 다시 만들 수 있어야 한다.
2. **화이트리스트로만 꺼낸다.** 원본(`survey`·`result`)을 통째로 복사하거나 "필요 없는 키를 빼는" 블랙리스트 방식으로 만들지 않는다. 엔진 결과에 새 필드가 생겨도 화이트리스트에 없으면 분석 저장소에 들어가지 않는다. 특히 `result.company`·`survey.company`에는 기업명과 자유서술이 들어 있다.
3. **사람은 가명키로만 잇는다.** 분석 테이블에는 `auth.users.id`가 없고 `subject_key`만 있다. 회원 ↔ 가명키 대응표는 별도 스키마 `private`에 둔다.
4. **분석용 스키마는 공개하지 않는다.** `analytics`·`private` 스키마는 Supabase Data API 노출 스키마에 넣지 않고, 모든 테이블에 RLS를 켜고(정책 없음), `anon`·`authenticated` 권한을 회수한다. 접근은 FastAPI 서버 연결로만 한다(11.1과 같은 원칙).
5. **동의한 회차만 넣는다.** 통계 활용 동의(`consents.kind = 'analytics'`, 철회되지 않은 것)가 있는 회원의 최종저장 회차만 넣는다. 이 동의는 가입 필수 동의다(12.2). 이미 넣은 분석 행은 회차 삭제·탈퇴 후에도 남는다(12.2).
6. **버전을 같이 저장한다.** 모든 행에 `model_version`·`questions_version`을 둔다. 새 모형으로 옛 회차를 다시 계산하면 기존 행을 덮어쓰지 않고 새 버전 행으로 추가한다. 집계는 버전을 섞지 않는다.
7. **게스트 진단은 넣지 않는다.** 게스트 응답은 브라우저에만 있다(9장 결정).
8. **원값을 저장하는 대신 노출은 집계로만 한다.** 매출·설립연도 같은 원값은 기업을 특정하는 단서가 될 수 있다. 그래서 개별 행은 관리자 내보내기(감사 기록) 외에는 밖으로 내보내지 않고, 화면·보고서에는 구간화한 집계만 내며 표본이 `k`(가설값 5) 미만인 칸은 숨긴다.

### 12.4 DNA 방향값 알고리즘

경영자 성향은 4축 각각을 **방향값** 하나로 저장한다. 방향값은 부호로 어느 쪽인지, 크기로 얼마나 치우쳤는지를 함께 나타내며, 축 점수를 그대로 역산할 수 있다.

**계산 (저장할 때)**

```
축 점수 D_k  = 엔진 결과 result.dna.axes[축].score   (0~100, 소수 둘째 자리, 계산식은 4.2절)
방향값 dir_k = (D_k − 50) × 2                         (−100 ~ +100)
응답 없는 축(score = null)은 dir_k = null, answered = 0
```

- `+`는 A 성향(G 성장확장, I 혁신차별, N 시장개척, P 조직체계), `−`는 B 성향(S 안정내실, E 효율경쟁, C 기존시장집중, O 창업자주도), `0`은 정중앙.
- `+100`은 그 축 6문항에 모두 5점, `−100`은 모두 1점.
- 축 점수가 소수 둘째 자리이므로 방향값도 소수 둘째 자리에서 정확하다(`numeric(5,2)`). 반올림 오차가 생기지 않도록 float가 아니라 엔진이 반올림한 `score`에서 계산한다.

**역산 (조회할 때)**

```
축 점수   = 50 + dir_k / 2
유형 문자 = dir_k ≥ (letter_cutoff − 50) × 2  이면 A, 아니면 B      (현재 letter_cutoff 50 → dir_k ≥ 0)
경계 여부 = (b_threshold − 50) × 2 < dir_k < (a_threshold − 50) × 2   (현재 40·60 → −20 < dir_k < +20)
치우침 크기 = |dir_k|
```

- 유형 문자·경계 여부는 **저장하지 않는다.** 기준값(`letter_cutoff`, `a_threshold`, `b_threshold`)은 가설값이므로 그 행의 `model_version` 설정 파일에서 읽어 조회 시점에 계산한다. 그래야 기준이 바뀌어도 데이터를 다시 만들지 않아도 된다.
- 4자리 유형 코드 `dna_type`은 엔진이 낸 값을 그대로 저장한다(유형별 집계 인덱스용). 역산한 문자와 다르면 버그다(테스트로 확인).
- 역산으로 되살릴 수 있는 것은 **축 점수까지**다. 개별 문항 응답은 되살릴 수 없다.

**구현 (예: `api/bizdna_api/analytics.py`)**

```python
def axis_direction(score: float | None) -> float | None:
    """축 점수(0~100) → 방향값(−100~+100)."""
    return None if score is None else round((score - 50) * 2, 2)


def axis_score(direction: float | None) -> float | None:
    """방향값 → 축 점수. axis_score(axis_direction(s)) == s 이어야 한다."""
    return None if direction is None else round(50 + direction / 2, 2)
```

**예시** (그린푸드랩형): G/S 75점 → `+50`, I/E 68점 → `+36`, N/C 42점 → `−16`(경계), P/O 30점 → `−40`. 저장: `dna_type = 'GICO'`, `dna_g_dir = 50.00`, `dna_i_dir = 36.00`, `dna_n_dir = -16.00`, `dna_p_dir = -40.00`.

**단위 테스트 필수 항목**: 왕복(`axis_score(axis_direction(s)) == s`, 0·40·50·60·100과 소수 점수), 응답 없는 축(null), 경계값(점수 40·60 → 방향 −20·+20은 경계 아님), 엔진 `dna_type`과 역산 문자 일치.

### 12.5 화이트리스트 (원본 → 분석 컬럼)

표에 없는 값은 모두 버린다.

| 원본 | 분석 컬럼 | 처리 |
| --- | --- | --- |
| `diagnoses.id` | `diagnosis_id` | 백필·재생성용. 분석가용 뷰에서는 뺀다 |
| `diagnoses.created_by` | — | 버림. 호출자가 `subject_key`로 바꿔 넘김 |
| `diagnoses.company_name`, `progress`, `status` | — | 버림 |
| `diagnoses.phase`, `model_version`, `questions_version`, `completed_at` | 같은 이름 | 원값 |
| `survey.company.industry` | `industry` | 원값 (제조업·서비스업·도소매업) |
| `survey.company.founded_year` | `founded_year` | 원값 |
| `survey.company.sales_recent`, `sales_prev` | `sales_recent`, `sales_prev` | 원값 (억원) |
| `survey.company.operating_margin` | `operating_margin` | 원값 (%) |
| `survey.company.employees` | `employees` | 원값 (명) |
| `survey.company.customer_type` | `customer_type text[]` | 원값 (선택지) |
| `survey.company.name`, `industry_detail`, `main_channel`, `goal_3y`, `investment_plan` | — | **버림** (기업명·자유서술) |
| `survey.answers.dna.*` (24문항) | — | 저장 안 함 → `result.dna`에서 방향값 |
| `survey.answers.competence.*` (64문항) | — | 저장 안 함 → `result.competence`에서 영역 점수 |
| `survey.answers.stage.{product, customer, revenue, cash, operations, expansion}` | `stage_product` … `stage_expansion` | 원값 1~5 |
| `survey.answers.plan.P01`~`P12` | `plan jsonb` | P코드 키만 골라 원값 (선택 코드 배열·숫자 금액·인원 그대로) |
| `survey.answers.plan.P01` | `goals text[]` | 원값 (인덱스·집계용 사본) |
| `survey.answers.plan.P09` 중 `model.risks`에 있는 코드 | `risk_flags text[]` | 엔진 위험 플래그 코드. `result.risks`는 한글 라벨이므로 쓰지 않는다 |
| `result.dna.type` | `dna_type` | 원값 |
| `result.dna.axes[축].score` | `dna_g_dir`, `dna_i_dir`, `dna_n_dir`, `dna_p_dir` | 12.4 방향값 |
| `result.dna.axes[축].answered` | `dna_g_answered` … `dna_p_answered` | 원값 (0~6) |
| `result.stage.code`, `weighted_index`, `provisional`, `gate_adjusted`, `gates_applied[].id` | `stage_code`, `stage_weighted_index`, `stage_provisional`, `stage_gate_adjusted`, `stage_gates text[]` | 원값 |
| `result.competence.total`, `grade.grade`, `missing_ratio` | `total_score`, `grade`, `competence_missing_ratio` | 원값 (정밀진단만, 기본진단은 null) |
| `result.competence.domains[A~H]` | `analytics.domain_scores` 8행 | 점수 원값, 그 회차 가중치, 응답 문항 수(8 − 그 영역의 `missing` 개수) |
| `result.strategies[]` 의 `code`, `factors.{fit, urgency, impact, feasibility}`, `score`, 순위, `status`, `applied_rules` | `analytics.strategy_scores` 12행 | 원값. 순위는 리스트 순서(1부터) |
| `result.dna.name`, `profile`, `strategies[].name`·`reasons`·`actions`·`kpis`, `result.company`, `result.plan`, `limitations`, `completeness` | — | **버림** (라벨은 설정 파일에서 붙이고, 나머지는 중복·식별정보) |

### 12.6 DB 설정 방법 (마이그레이션)

마이그레이션 파일 하나(`supabase/migrations/<타임스탬프>_analytics.sql`)로 만들고 `scripts/migrate.py`로 적용한다. 대시보드에서 손으로 만들지 않는다(11.2).

**순서**

1. 스키마 `private`, `analytics` 생성 → 권한 회수
2. `public.consents.kind`에 `'analytics'` 추가 (기존 check 제약을 바꾼다)
3. `private.subject_map` → `analytics.*` 테이블 생성
4. 모든 새 테이블 RLS 켜기(정책 없음), 인덱스 생성
5. 가명키 발급 함수 `private.get_subject_key(user_id)` 생성
6. 적용 후 확인: Supabase 대시보드 Settings → API의 **Exposed schemas에 `analytics`·`private`이 없는지**, 공개 키로 `/rest/v1/diagnosis_facts`를 호출했을 때 거부되는지

**SQL 초안**

```sql
-- 1. 스키마와 권한 -------------------------------------------------------------
create schema if not exists private;
create schema if not exists analytics;
revoke all on schema private, analytics from public, anon, authenticated;
alter default privileges in schema private, analytics revoke all on tables from public, anon, authenticated;

-- 2. 통계 활용 동의 종류 추가 --------------------------------------------------------
alter table public.consents drop constraint if exists consents_kind_check;
alter table public.consents add constraint consents_kind_check
  check (kind in ('privacy', 'storage', 'ai', 'analytics'));

-- 3. 가명키 대응표 (회원 탈퇴 시 함께 지워져 분석 행은 누구 것인지 알 수 없게 된다) -------------
create table private.subject_map (
  user_id     uuid primary key references auth.users (id) on delete cascade,
  subject_key uuid not null unique default gen_random_uuid(),
  created_at  timestamptz not null default now()
);

-- 4. 진단 회차 팩트 (회차 × 모형 버전 1행) ---------------------------------------------
create table analytics.diagnosis_facts (
  fact_id            uuid primary key default gen_random_uuid(),
  diagnosis_id       uuid not null,            -- FK 없음: 원본 삭제 시 처리는 12.10 미결정
  model_version      text not null,
  questions_version  text not null,
  subject_key        uuid not null,
  round_no           int  not null check (round_no >= 1),
  phase              text not null check (phase in ('basic', 'full')),
  completed_at       timestamptz not null,
  -- 기업정보 (원값)
  industry           text,
  founded_year       int,
  sales_recent       numeric,
  sales_prev         numeric,
  operating_margin   numeric,
  employees          int,
  customer_type      text[],
  -- 경영자 성향 (12.4 방향값)
  dna_type           text,
  dna_g_dir          numeric(5,2) check (dna_g_dir between -100 and 100),
  dna_i_dir          numeric(5,2) check (dna_i_dir between -100 and 100),
  dna_n_dir          numeric(5,2) check (dna_n_dir between -100 and 100),
  dna_p_dir          numeric(5,2) check (dna_p_dir between -100 and 100),
  dna_g_answered     smallint not null default 0,
  dna_i_answered     smallint not null default 0,
  dna_n_answered     smallint not null default 0,
  dna_p_answered     smallint not null default 0,
  -- 성장단계 (원값)
  stage_product      smallint, stage_customer smallint, stage_revenue smallint,
  stage_cash         smallint, stage_operations smallint, stage_expansion smallint,
  stage_code         text,
  stage_weighted_index numeric,
  stage_provisional  text,
  stage_gate_adjusted boolean,
  stage_gates        text[],
  -- 역량 요약 (정밀진단만)
  total_score        numeric,
  grade              text,
  competence_missing_ratio numeric,
  -- 성장계획·제약 (원값)
  goals              text[],
  risk_flags         text[],
  plan               jsonb,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique (diagnosis_id, model_version)
);

create table analytics.domain_scores (
  fact_id  uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  domain   char(1) not null check (domain in ('A','B','C','D','E','F','G','H')),
  score    numeric,                 -- 영역 전체 결측이면 null
  weight   numeric not null,        -- 그 회차 모형 버전의 가중치
  answered smallint not null,
  primary key (fact_id, domain)
);

create table analytics.strategy_scores (
  fact_id     uuid not null references analytics.diagnosis_facts (fact_id) on delete cascade,
  strategy    text not null,        -- ST01~ST12
  fit         numeric, urgency numeric, impact numeric, feasibility numeric,
  total       numeric not null,
  rank        smallint not null,
  status      text not null check (status in ('recommended', 'deferred')),
  rule_ids    text[] not null default '{}',
  primary key (fact_id, strategy)
);

create table analytics.funnel_events (
  id           bigint generated always as identity primary key,
  subject_key  uuid not null,
  diagnosis_id uuid not null,
  event        text not null check (event in ('started', 'basic_completed', 'full_completed', 'report_downloaded')),
  occurred_at  timestamptz not null default now()
);

-- 5. RLS (정책 없음 = Data API 직접 접근 차단, FastAPI 서버 연결만 사용) ----------------
alter table private.subject_map        enable row level security;
alter table analytics.diagnosis_facts  enable row level security;
alter table analytics.domain_scores    enable row level security;
alter table analytics.strategy_scores  enable row level security;
alter table analytics.funnel_events    enable row level security;

-- 6. 인덱스 ---------------------------------------------------------------------
create index on analytics.diagnosis_facts (industry, stage_code);
create index on analytics.diagnosis_facts (dna_type);
create index on analytics.diagnosis_facts (subject_key, round_no);
create index on analytics.diagnosis_facts (model_version);
create index on analytics.funnel_events (subject_key, event);

-- 7. 가명키 발급 (없으면 만들고, 있으면 그대로 돌려준다) -------------------------------------
create or replace function private.get_subject_key(p_user_id uuid) returns uuid
language sql as $$
  with ins as (
    insert into private.subject_map (user_id) values (p_user_id)
    on conflict (user_id) do nothing
    returning subject_key
  )
  select subject_key from ins
  union all
  select subject_key from private.subject_map where user_id = p_user_id
  limit 1;
$$;
revoke all on function private.get_subject_key(uuid) from public, anon, authenticated;
```

`gen_random_uuid()`는 Supabase Postgres에 기본으로 있다. 적용 전에 기존 consents check 제약 이름이 `consents_kind_check`인지 확인한다(이름이 다르면 그 이름으로 지운다).

### 12.7 수집 흐름 (API)

```
최종저장 (POST/PUT /api/diagnoses, complete=basic|full)
  ① public.diagnoses에 survey·result·버전 저장 (지금과 같음)
  ② 같은 트랜잭션에서:
     - 통계 활용 동의 확인: consents에 kind='analytics', withdrawn_at is null 인 행이 있는가 → 없으면 끝
     - subject_key = private.get_subject_key(user_id)
     - round_no  = 같은 diagnosis_id의 기존 팩트가 있으면 그 round_no,
                   없으면 coalesce(max(round_no), 0) + 1  (그 subject_key 기준)
     - rows = derive_rows(diagnosis_row, subject_key=..., round_no=...)
     - diagnosis_facts upsert: on conflict (diagnosis_id, model_version) do update
     - domain_scores·strategy_scores: 그 fact_id 행을 지우고 다시 넣는다
     - funnel_events에 basic_completed 또는 full_completed 추가
```

- `derive_rows`와 방향값 함수는 `api/bizdna_api/analytics.py`에 둔다. 엔진(`api/engine`)은 고치지 않는다. 반환값은 `AnalyticsRows(fact: dict, domain_scores: list[dict], strategy_scores: list[dict])` 데이터클래스로 하고, 기본진단(`result.competence`가 null)이면 두 목록은 비어 있다.
- 지금 `PostgresStore.update`는 메서드마다 연결을 열고 바로 커밋한다. ①과 ②를 한 트랜잭션으로 묶으려면 저장소에 최종저장 전용 메서드(예: `complete(user_id, diagnosis_id, data, analytics_writer)`)를 추가하거나 연결을 넘기는 구조로 바꾼다. `MemoryStore`도 같은 동작을 흉내 내 테스트한다.
- 분석 저장이 실패해도 진단 저장은 실패시키지 않을지(②를 별도 트랜잭션으로 둘지)는 구현 때 정한다. 기본안은 **같은 트랜잭션**(원본과 분석이 어긋나지 않게)이다.
- 중간저장(`draft`)은 팩트를 만들지 않는다. 처음 회차를 만들 때(`POST`) 동의한 회원이면 `started` 이벤트만 남긴다. PDF를 받을 때 `report_downloaded`를 남기려면 `/api/report`가 회원을 알아야 하므로 나중에 추가한다.
- **동의 철회**: 통계 활용 동의가 가입 필수 동의가 되었으므로 철회 기능은 따로 만들지 않았다. 철회 기능을 만들게 되면 분석 행을 지울지 다시 정한다(12.2 결정은 "남긴다").
- **백필**: `scripts/backfill_analytics.py`가 동의한 회원의 완료 회차(`status in ('basic_completed','full_completed')`)를 `completed_at` 순으로 돌며 같은 upsert를 실행한다. 여러 번 돌려도 결과가 같아야 한다(멱등). 새 모형 버전으로 다시 계산할 때는 엔진을 다시 돌린 결과로 새 `model_version` 행을 추가한다.

### 12.8 집계 뷰 (예시)

개별 행은 원값이지만, 화면·보고서·운영기관에 내보내는 것은 아래 집계뿐이다. 구간 경계값은 가설값이므로 `api/engine/bizdna/config/analytics_v1.json`(신규)에 두고 집계 함수가 읽는다. 초안: 업력 <3·3–7·7–15·15+년(진단 완료 연도 − 설립연도), 인력 <5·5–9·10–49·50–299·300+명, 매출 <1·1–10·10–50·50–120·120+억, 성장률 감소(<−5%)·유지·성장(+5~30%)·고성장(30%+), 이익률 적자·0–5·5–10·10+%, `k = 5`. 모든 구간은 하한 포함·상한 미포함.

| 뷰 | 내용 | 쓰는 곳 |
| --- | --- | --- |
| `v_dna_direction` | 업종·단계·규모 구간별 4축 방향값 평균·분포, 유형 빈도, 경계 비율 | 운영기관 화면(FR-19), 결과 화면의 "같은 업종 경영자 성향" |
| `v_domain_percentiles` | 업종·규모·단계별 역량 영역 점수 분위(p25·p50·p75) | 결과·보고서의 유사집단 비교 |
| `v_stage_gates` | 단계별 Gate 적용 빈도와 6지표 분포 | 성장단계 모형 검토 |
| `v_strategy_frequency` | 전략별 1–3순위 추천 빈도, 보류 사유 빈도 | 전략 매칭 매트릭스 검토 |
| `v_constraints` | 성장장애(P09)·목표(P01)·지원수요(P12) 분포 | 정책수요 분석(FR-19) |
| `v_retest` | 같은 `subject_key`의 연속 회차 쌍: 유형 일치, 축별 방향값 변화, 단계·점수 변화, 간격 | 유형 안정성, 재진단 변화(FR-16) |
| `v_funnel` | 월별 시작 → 기본완료 → 정밀완료, 재진단율 | 사용 지표 |

- 모든 집계는 표본 수 `n`을 함께 내고, `n < k`인 칸은 **API에서** 숨기거나 상위 범주로 합친다(뷰가 아니라 API에서 일관되게 처리해 우회를 막는다).
- 모형 버전이 다른 회차를 한 집계에 섞지 않는다.
- 무거운 뷰는 머티리얼라이즈드 뷰로 두고 하루 한 번 갱신한다(Vercel Cron 또는 `pg_cron`, 12.10).

### 12.9 접근 권한과 나중에 추가할 것

- **관리자**: 모든 집계와 개별 팩트 행(목록·상세)을 화면에서 보고 CSV로 내보낸다(2026-11-18 결정으로 변경). 조회·내보내기마다 `private.audit_logs`에 기록한다. 관리자 화면에는 `k` 숨김을 적용하지 않고 `n`을 함께 보인다(`docs/admin.md`).
- **운영기관**: 소속 사업 기업(`program_enrollments`)의 **집계만** 본다. `memberships` 생성 후 구현한다.
- **컨설턴트**: 담당 기업은 원본(`public.diagnoses`)으로 보고, 분석 저장소에서는 유사집단 비교 값만 받는다.
- **기업 담당자**: 자기 결과 화면에서 유사집단 비교(분위·비율)만 본다.
- 외부 분석 도구에 DB 계정을 주지 않는다. 필요하면 `analytics`의 뷰에만 읽기 전용 역할을 따로 만든다.
- **문항 단위 응답이 필요해지면**(시범검증의 α·변별도): `analytics.answer_items(fact_id, section, code, value, scored, is_missing)`를 추가하고 백필로 채운다. 원본에서 회차를 삭제한 경우는 복구할 수 없다.

### 12.10 미결정 사항 (구현 전에 사용자 확인)

- [x] 통계 활용 동의: 가입 필수 동의에 포함 (2026-11-18). 이전 가입자에게 다시 받는 방법은 미정(지금은 수집 안 됨)
- [x] 회차 삭제·탈퇴 시 분석 행: 남긴다(가명 상태) (2026-11-18). 개인정보처리방침에 이 내용을 적어야 한다
- [x] 분석 저장 실패 시 진단 저장도 실패: 같은 트랜잭션으로 구현 (2026-11-18)
- [ ] 원값으로 저장하는 매출·영업이익률 등 재무 필드의 컬럼 단위 추가 암호화 여부(9장·11.4 항목과 같이 결정)
- [ ] 집계용 구간 경계와 소수 집단 기준 `k` 확정(12.8 초안)
- [ ] 시범검증 원자료를 외부 연구자와 공유할지, 공유 형식
- [ ] 집계 갱신 주기와 도구(Vercel Cron vs `pg_cron`)
- [x] 수집 함수 형태, 회차당 1행, DNA 방향값, 원값 저장, 문항 응답 미저장 (2026-11-18, 12.2)
- [x] DB 리전: 뭄바이(ap-south-1) 유지 (2026-11-18, 11.2)

### 12.11 구현 순서 (권장)

1. 12.10의 동의·삭제 정책을 먼저 정한다.
2. 12.6 마이그레이션 작성·적용, Data API 비노출 확인.
3. `analytics.py`: `axis_direction`·`axis_score`·`derive_rows` + 단위 테스트(12.4 필수 항목, 기본/정밀 진단, 결측 축·영역, **화이트리스트 밖 값이 행에 없는지**: 기업명·자유서술·회원 ID 문자열을 넣은 입력으로 결과 전체를 검사).
4. 최종저장 API에서 같은 트랜잭션으로 upsert, 동의 철회 시 삭제. 권한·동의 없음 테스트 포함.
5. 백필 스크립트로 기존 회차 채우기(멱등 테스트).
6. 집계 뷰와 관리자 조회 API(k 처리 포함), 이후 운영기관 화면(FR-19)과 결과 화면의 유사집단 비교.

### 12.12 지금 저장 구조에서 미리 알아 둘 점

- `public.diagnoses.result`에는 엔진 출력 그대로 `company` 전체(기업명 포함)가, `survey.company`에도 기업명과 자유서술이 들어 있다. 파생 함수는 반드시 12.5 화이트리스트로만 꺼낸다.
- `diagnoses.company_id`는 아직 비어 있다. 지금 가명키는 **회원 기준**이라 한 기업을 담당자가 바뀌어 재진단하면 다른 사람처럼 보인다. `companies`가 생기면 가명키를 기업 기준으로 바꿀지 정한다(재진단 추적에는 기업 기준이 유리하다).

### 12.13 구현하면서 설계와 달라진 점 (2026-11-18)

- **마이그레이션**: 12.6 SQL에 더해 `public.memberships`(관리자 역할), `private.audit_logs`, 가입 트리거의 `analytics` 동의 처리, `funnel_events`의 `unique (diagnosis_id, event)`(재저장해도 이벤트가 늘지 않게)를 넣었다.
- **이벤트**: 정밀진단 완료를 저장하면 `basic_completed`도 함께 남긴다(정밀은 기본을 거치므로). 그래야 "기본 완료 ≥ 정밀 완료"가 성립한다.
- **P문항 원값**: 화이트리스트 키라도 설정(`questions_v1.json`)의 선택지·숫자 형식에 맞는 값만 남긴다. 자유 문자열이 섞여 들어오지 않게 하기 위해서다. 업종·주요 고객도 선택지에 없는 값은 버린다.
- **트랜잭션 보호**: 풀러 연결이 트랜잭션 도중 끊겨 DB 쪽에 잠금이 남는 일이 실제로 있었다. 모든 API 트랜잭션에 `lock_timeout 5s`·`idle_in_transaction_session_timeout 20s`·`statement_timeout 20s`를 `set_config(..., true)`로 건다. 역량·전략 행은 한 문장으로 넣어 왕복을 줄였다.
- **집계 위치**: 12.8의 DB 뷰 대신, 지금은 API가 필터에 맞는 행(최대 5,000건)을 읽어 `summarize_facts`로 계산한다. 회차가 많아지면 뷰·머티리얼라이즈드 뷰로 옮긴다.
