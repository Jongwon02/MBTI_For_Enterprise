# legacy/mvp_integrated — ChatGPT 소상공인 통합 플랫폼 MVP 원본 (수정 금지, 참고용)

출처: ChatGPT 대화(https://chatgpt.com/share/6b03f3a9-3504-83ee-9ab9-1015596447fb)의 "소상공인 Biz-DNA 통합형 온라인 경영진단 플랫폼" 단계에서 만든 Streamlit MVP. 대화의 다운로드 링크는 만료됐고, 사용자가 2026-11-23에 파일을 직접 전달해 보관했다. 원래 README는 `README_original.md`로 이름을 바꿨다.

| 파일 | 내용 |
| --- | --- |
| `engine.py` | 진단엔진. **DNA 16문항 지문(`DNA`)**, 역량 32문항(`QUESTIONS`, mvp_v1보다 다듬은 문구), 영역 가중치, 영역별 전략, 업종 가산점(`SECTOR_BONUS`), 위험 규칙 4개 |
| `app.py` | Streamlit 화면 (점포정보 → DNA 16 → 역량 32 → 결과·PDF) |
| `report.py` | ReportLab 기본형·정밀형 PDF |
| `test_engine.py` | 샘플 2개 진단 + PDF 생성 확인 |
| `sample_cafe.json`, `sample_service.json` | 가상 점포 입력 (CLAUDE.md 4.9 기준 사례) |
| `sample_*_basic.pdf`, `sample_*_detailed.pdf` | 이 MVP가 생성한 보고서 |

2026-11-23 Python 3으로 `engine.diagnose`를 실행해 확인한 결과 (대화에 나온 값과 일치):

- 동네카페: GDRO, 종합 48.75, 위험 WEAK_FINANCE, 1~3순위 수익구조 및 현금흐름 개선(73.65) → 신규고객 유입 강화(65.25) → 디지털 경영관리 도입(63.25)
- 우리동네수리: SDRO, 종합 55.0, 위험 없음, 1~3순위 단골고객 및 재방문 확대(73.65) → 신규고객 유입 강화(69.45) → 디지털 경영관리 도입(63.25)

같이 전달된 `legacy_mvp.py`는 `../mvp_v1/app.py`와 같은 파일이라 다시 보관하지 않았다.
