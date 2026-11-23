# legacy/mvp_v4 — ChatGPT 소상공인 v4.0 원본 (수정 금지, 참고용 · 엔진 v1 재현 기준)

출처: ChatGPT 대화(https://chatgpt.com/share/6b03f3a9-3504-83ee-9ab9-1015596447fb)의 "Biz-DNA 소상공인 경영진단 시스템 v4.0 고도화" 단계(Streamlit). 대화의 다운로드 링크는 만료됐고, 사용자가 2026-11-23에 파일을 직접 전달해 보관했다. 원래 README는 `README_original.md`로 이름을 바꿨다.

| 파일 | 내용 |
| --- | --- |
| `engine.py` | 공통 엔진(모형 `3.0-prototype`): DNA 16문항, 역량 32문항, 기본 가중치, 영역별 전략, 업종 가산점, 위험 규칙 5개, 경영목표 가산, 적자 시 확장 전략 제한 |
| `advanced.py` | v4(모형 `4.0-pilot`): **업종 특화 12문항(3업종 × 3영역 × 4)**, **업종별 가중치**, 특화점수 혼합(공통 65% + 특화 35%), 실적 기반 잠정 성장단계(S1~S4), 진단 신뢰도, 사용자 입력 비교기준 |
| `app.py` | Streamlit 화면 |
| `report.py` | ReportLab PDF (성장단계·신뢰도 줄이 추가된 것 외에는 mvp_integrated와 같다) |
| `test_v4.py` | 특화문항·실적 입력 시 S4·신뢰도 "보통" 확인 + PDF |
| `sample_*.json` | 기본 입력 (mvp_integrated와 같은 값) |
| `example_*_v4.json` | 특화문항·실적까지 넣은 입력 |
| `example_*_result.json`, `example_*.pdf` | v4가 만든 결과와 보고서 |

2026-11-23 Python 3으로 `advanced.diagnose_v4`를 실행해 `example_*_result.json`과 같은 값이 나오는 것을 확인했다(동네카페 GDRO 47.92 S3, 우리동네수리 SDRO 54.66 S3). 기대값은 CLAUDE.md 4.9에 있다.
