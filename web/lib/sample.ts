// 데모용 가상기업(그린푸드랩) 응답. engine/tests/fixtures.py의 case_a에서 생성했다. 실제 기업 자료가 아니다.
import type { Survey } from "./types";

export const SAMPLE_SURVEY: Survey = {
  "company": {
    "name": "그린푸드랩",
    "industry": "제조업",
    "industry_detail": "건강간편식 제조",
    "founded_year": 2023,
    "sales_recent": 8,
    "employees": 7,
    "customer_type": [
      "기업(B2B)",
      "소비자(B2C)"
    ],
    "sales_prev": 6.5,
    "operating_margin": 3.5,
    "main_channel": "온라인몰, 식품 유통사",
    "goal_3y": "3년 내 매출 20억 원, 신규 유통채널 2곳 확보",
    "investment_plan": "생산설비 증설 2억 원"
  },
  "answers": {
    "dna": {
      "D01": 5,
      "D02": 4,
      "D03": 4,
      "D04": 4,
      "D05": 4,
      "D06": 4,
      "D07": 5,
      "D08": 5,
      "D09": 4,
      "D10": 4,
      "D11": 4,
      "D12": 4,
      "D13": 3,
      "D14": 3,
      "D15": 2,
      "D16": 2,
      "D17": 2,
      "D18": 2,
      "D19": 3,
      "D20": 2,
      "D21": 2,
      "D22": 2,
      "D23": 2,
      "D24": 2
    },
    "stage": {
      "product": 4,
      "customer": 3,
      "revenue": 3,
      "cash": 2,
      "operations": 3,
      "expansion": 3
    },
    "competence": {
      "A01": 4,
      "A02": 4,
      "A03": 4,
      "A04": 4,
      "A05": 4,
      "A06": 3,
      "A07": 3,
      "A08": 3,
      "B01": 4,
      "B02": 4,
      "B03": 3,
      "B04": 3,
      "B05": 3,
      "B06": 3,
      "B07": 3,
      "B08": 3,
      "C01": 5,
      "C02": 5,
      "C03": 5,
      "C04": 4,
      "C05": 4,
      "C06": 4,
      "C07": 4,
      "C08": 4,
      "D01": 3,
      "D02": 3,
      "D03": 3,
      "D04": 3,
      "D05": 3,
      "D06": 3,
      "D07": 2,
      "D08": 2,
      "E01": 3,
      "E02": 3,
      "E03": 3,
      "E04": 3,
      "E05": 3,
      "E06": 2,
      "E07": 2,
      "E08": 2,
      "F01": 4,
      "F02": 4,
      "F03": 4,
      "F04": 4,
      "F05": 4,
      "F06": 4,
      "F07": 3,
      "F08": 3,
      "G01": 3,
      "G02": 3,
      "G03": 3,
      "G04": 3,
      "G05": 3,
      "G06": 3,
      "G07": 2,
      "G08": 2,
      "H01": 4,
      "H02": 4,
      "H03": 4,
      "H04": 4,
      "H05": 4,
      "H06": 4,
      "H07": 4,
      "H08": 4
    },
    "plan": {
      "P01": [
        "profit",
        "market",
        "funding"
      ],
      "P09": [
        "negative_unit_margin",
        "founder_bottleneck",
        "funding_gap"
      ],
      "P02": 20,
      "P03": 15,
      "P04": 2,
      "P05": [
        "facility",
        "marketing"
      ],
      "P06": 1.5,
      "P07": "develop",
      "P08": "review",
      "P10": [
        "money",
        "people"
      ],
      "P11": [
        "cashflow",
        "pricing"
      ],
      "P12": [
        "finance",
        "marketing"
      ]
    }
  }
};
