# Biz-DNA 2.0 통합 자동보고서

## 기능
- 기존 Biz-DNA 1.0 진단엔진 활용: DNA 16유형, 8대 역량, 5단계 성장단계, 위험 플래그, 전략 12종
- 기본형 PDF: 5개 핵심 장(표지/요약 포함, 페이지 수는 데이터 길이에 따라 가변)
- 정밀형 PDF: 15개 분석 장(페이지 수는 데이터 길이에 따라 가변)
- 8대 역량 막대그래프, 전략 추천점수, 성장 로드맵, KPI, 보류전략
- AI 심층해석: OPENAI_API_KEY 환경변수 설정 시 선택적 호출. API 키 미설정 시 규칙기반 보고서로 안전하게 생성.

## 로컬 실행
```bash
python -m pip install -r requirements.txt
uvicorn api:app --host 127.0.0.1 --port 8000
```
브라우저에서 http://127.0.0.1:8000 을 열고 `case_a.json` 또는 `case_b.json` 내용을 붙여넣으세요.

## API
- `POST /diagnose` : 기업 입력 JSON을 요청 본문에 직접 전달
- `POST /report` : `{ "payload": <기업 입력 JSON>, "mode": "basic" | "advanced", "use_ai": false }`
- 반환: application/pdf

## 명령행 예시
```bash
python -c "import json;from reports import generate;generate(json.load(open('case_a.json',encoding='utf-8')),'sample_basic.pdf','basic');generate(json.load(open('case_b.json',encoding='utf-8')),'sample_advanced.pdf','advanced')"
```

## AI 사용(선택)
```bash
export OPENAI_API_KEY='사용자 본인 API 키'
export BIZDNA_AI_MODEL='gpt-4.1-mini'
```
AI 요청 시 기업진단 결과 일부가 외부 AI API에 전송됩니다. 기업 동의, 개인정보·영업비밀 보호 및 이용약관 검토 후 활성화하세요.

## 시범모형 한계
- 가중치, 성장단계 임계값, 유형 분류기준은 통계적으로 검증되지 않은 가설값입니다.
- 재무 수치·매출 등의 입력값은 진단엔진이 독립적으로 검증하지 않습니다.
- AI 문장은 보조 해석이며 전략순위·수치·진단 결과는 규칙기반 엔진이 결정합니다.
- 데모 웹 UI는 인증·DB 저장·다중 사용자 권한·결제 기능이 없습니다. 운영환경 배포 전 추가 필요.
