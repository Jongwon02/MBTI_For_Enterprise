"""PRD 8.7 기준 사례. legacy/bizdna/create_examples.py의 생성 방식을 그대로 옮겼다."""
import copy


def make(name, industry, dna, domains, stage, goals, flags):
    answers = {"dna": {}, "competence": {}, "stage": stage}
    for i, score in enumerate(dna):
        # 축당 6문항. 목표 평균을 정수 응답으로 번갈아 배분한다.
        total = round(6 + score / 100 * 24)
        values = [1] * 6
        for j in range(total - 6):
            values[j % 6] += 1
        for j, v in enumerate(values):
            answers["dna"][f"D{i * 6 + j + 1:02d}"] = v
    for d, score in domains.items():
        total = round(8 + score / 100 * 32)
        values = [1] * 8
        for j in range(total - 8):
            values[j % 8] += 1
        for j, v in enumerate(values):
            answers["competence"][f"{d}{j + 1:02d}"] = v
    return {"company": {"name": name, "industry": industry}, "answers": answers, "goals": goals, "flags": flags}


CASES = {
    "case_a": make("그린푸드랩", "식품제조", [78, 82, 35, 30], dict(zip("ABCDEFGH", [65, 55, 85, 45, 40, 70, 45, 75])),
                   {"product": 4, "customer": 3, "revenue": 3, "cash": 2, "operations": 3, "expansion": 3},
                   ["profit", "market", "funding"], {"negative_unit_margin": True, "founder_bottleneck": True, "funding_gap": True}),
    "case_b": make("넥스트솔루션", "B2B SaaS", [92, 88, 85, 38], dict(zip("ABCDEFGH", [80, 85, 90, 65, 50, 65, 80, 75])),
                   {"product": 5, "customer": 4, "revenue": 5, "cash": 4, "operations": 3, "expansion": 4},
                   ["scale", "market"], {"founder_bottleneck": True, "service_overload": True}),
}


def case(name):
    return copy.deepcopy(CASES[name])


def as_survey(payload):
    """엔진 입력을 웹 설문 응답 구조로 바꾼다."""
    return {
        "company": {"name": payload["company"]["name"], "industry": "제조업", "industry_detail": payload["company"]["industry"],
                    "founded_year": 2023, "sales_recent": 8, "employees": 7, "customer_type": ["기업(B2B)"]},
        "answers": {"dna": payload["answers"]["dna"], "stage": payload["answers"]["stage"],
                    "competence": payload["answers"]["competence"],
                    "plan": {"P01": payload["goals"], "P09": [k for k, v in payload["flags"].items() if v]}},
    }
