# legacy — ChatGPT 시제품 원본 (수정 금지, 참고용)

출처: https://chatgpt.com/share/6af7f207-27bc-83ee-a43b-b5e628d312d2 대화의 도구 호출(heredoc)에서 원문 그대로 추출했다. 2026-11-15에 Windows 11과 Python 3.12에서 실행해 확인했다.

| 폴더 | 내용 |
| --- | --- |
| `bizdna/` | 1.0 진단엔진 `engine.py`, 사례 생성 `create_examples.py`, 테스트 `test_engine.py`, 초기 보고서 `report_generator.py`. `case_*.json`·`result_*.json`은 실행으로 생성한 파일 |
| `BizDNA_Integrated/` | 2.0 보고서 `reports.py`, FastAPI `api.py`. `engine.py`와 `case_*.json`은 원래 스크립트대로 `bizdna/`에서 복사한 것 |
| `samples/` | 2.0으로 생성한 기본형(6쪽)·정밀형(16쪽) PDF 4개 (폰트는 맑은 고딕으로 바꿔 생성) |

## 검증 결과

- `python -m unittest -v test_engine`: 6개 모두 통과
- 결과가 PRD 8.7과 일치한다.
  - 그린푸드랩: GICO · S3 · 61.87 · ST07(81.72) → ST06(71.34) → ST08(61.69). ST03·ST11 보류(단위경제성)
  - 넥스트솔루션: GINO · S4 · 75.16 · ST08(71.09) → ST09(65.75) → ST03(65.17)
- 2.0 API(TestClient): `/diagnose` 200, `/report` 200(PDF), 잘못된 goals → 422, `/` 200

## 실행 시 주의

- 1.0은 외부 패키지 없이 실행된다: `cd bizdna && python create_examples.py && python -m unittest -v test_engine`
- 2.0은 `reportlab`, `fastapi` 등이 필요하다. `reports.py`의 폰트 경로가 리눅스용(`/usr/share/fonts/truetype/nanum/NanumSquare*.ttf`)이라 Windows에서는 그대로 실행되지 않는다. 대체 경로 `fc-match`도 없다. 검증할 때는 복사본에서만 `C:/Windows/Fonts/malgun.ttf`·`malgunbd.ttf`로 바꿨다.
