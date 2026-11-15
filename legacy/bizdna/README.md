# Biz-DNA 1.0 진단엔진 (프로토타입)

Python 3.10+ / 외부 패키지 불필요.

## 실행
```bash
python create_examples.py
python engine.py case_a.json
python engine.py case_b.json
python -m unittest -v test_engine.py
```

## 입력 구조
- `company`: 기업명·업종 등의 메타데이터
- `answers.dna`: `D01`~`D24`, 각 1~5점. 6문항씩 G/S, I/E, N/C, P/O 축
- `answers.competence`: `A01`~`H08`, 각 1~5점. 영역별 8문항
- `answers.stage`: `product`, `customer`, `revenue`, `cash`, `operations`, `expansion` 각각 1~5점
- `goals`: `profit`, `market`, `product`, `scale`, `funding`, `stability` 중 선택
- `flags`: `cash_crisis`, `market_unvalidated`, `negative_unit_margin`, `founder_bottleneck`, `capacity_shortage`, `funding_gap`, `service_overload` 등 boolean

## 출력
DNA 유형·축별 점수·경계 여부, 8대 영역 점수·가중 종합점수, 성장단계·Gate 조정, 위험요인, 12개 전략별 적합성/시급성/효과/실행가능성 점수, 보류 사유, 상위 추천전략.

## 운영 주의사항
- 시범 규칙 및 가중치는 검증되지 않았으며 정책적 지원 적격성·대출심사·투자결정 등에 직접 사용하지 말 것.
- 응답 누락은 오류로 처리. 생산 환경에서는 문항 분기·해당 없음·결측 규칙을 별도 구현.
- DNA 문항은 오른쪽 선택지가 5점인 양극형이며 역문항이 없는 시범구조.
- 단계 판정은 별도 입력된 6개 성숙도 평가에 의존. 평가기준표 및 객관증빙 수집은 후속 과제.
- 전략의 `impact`, `feasibility`는 임시 휴리스틱. 실제 기대효과 예측이나 투자수익률이 아님.
- 개인정보·재무정보의 접근제어, 암호화, 감사로그, 동의, 삭제, 버전관리 및 인증은 상용 API에서 별도 구현.
