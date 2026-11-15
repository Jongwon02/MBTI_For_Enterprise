# Biz-DNA (가칭) 중소기업 경영진단 플랫폼

요구사항은 `Biz-DNA 중소기업 경영진단 플랫폼 PRD.md`, 작업 규칙은 `CLAUDE.md`를 따른다.

## 실행 (Windows)

`run_dev.bat`을 더블클릭한다. 처음 실행할 때는 Python 가상환경과 npm 패키지를 설치하고, 그다음 API 서버(8000)와 웹 서버(3000) 창을 띄운 뒤 http://localhost:3000 을 연다.

직접 실행하려면:

```bash
# API (api 폴더에서)
../.venv/Scripts/python -m uvicorn bizdna_api.main:app --reload --port 8000
# 웹 (web 폴더에서)
npm run dev
```

필요 프로그램: Python 3.12 이상, Node.js 22 이상.

## 테스트

```bash
.venv/Scripts/python -m pytest api      # 엔진·API (기준 사례 회귀 포함)
cd web && npx tsc --noEmit && npm run lint && npm run build
```

## 구조

| 폴더 | 내용 |
| --- | --- |
| `api/engine/` | 진단엔진(Python, 순수 함수). 설정은 `api/engine/bizdna/config/*.json` |
| `api/` | FastAPI: 문항 제공, 진단, PDF 보고서. `api/fonts/`는 PDF용 나눔고딕(OFL) |
| `web/` | Next.js: 메인, 진단 설문, 결과 대시보드 |
| `docs/` | 문항 원문, 1.0 엔진 명세, 디자인 시스템 |
| `legacy/` | ChatGPT 시제품 원본(수정 금지) |
| `prototype/` | 메인 화면 디자인 시안(HTML) |

## 배포 (Vercel)

루트 `vercel.json`의 Services 설정으로 `web`(Next.js)과 `api`(FastAPI)를 한 프로젝트(`21111/mbti-for-enterprise`)에 배포한다. `/api/*`는 api 서비스, 나머지는 web 서비스로 간다.

```bash
npx vercel@latest deploy          # 미리보기
npx vercel@latest deploy --prod   # 운영
```
