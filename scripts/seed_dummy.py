"""관리자 화면·수집 확인용 더미 경영자 진단 만들기·지우기(docs/admin.md). **실제 기업 데이터가 아니다.**

실행 (저장소 루트에서):
  .venv/Scripts/python scripts/seed_dummy.py --count 100      # 더미 진단 100건 만들기
  .venv/Scripts/python scripts/seed_dummy.py --clean          # 더미 계정·진단·분석 행 모두 지우기

- 더미 회원 아이디는 `dummy_` 로 시작한다(지울 때 이 접두어로 찾는다). 약관 버전은 `dummy`.
- 일부 회원은 2회차(재진단)를 갖는다. 2회차는 1회차 성향을 조금 흔든 값이다.
- 경영자 성향: 회원마다 축별로 한쪽 성향을 정하고 그쪽으로 치우친 응답을 만든다. 축 점수가 경계 구간
  (37.5 초과 62.5 미만)에 들면 다시 뽑으므로 **중립·경계 값이 없다**. 업종별로 치우치는 방향의 확률도 다르다.
- 진단 결과는 실제 엔진(diagnose_survey)으로 계산하고, 서비스와 같은 저장 경로(PostgresStore)로 넣어 수집까지 확인한다.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "api" / "engine"))

import psycopg  # noqa: E402
from bizdna import diagnose_survey, load_questions  # noqa: E402

from bizdna_api import settings  # noqa: E402
from bizdna_api.signup import username_to_email  # noqa: E402
from bizdna_api.store import PostgresStore, _clean_url  # noqa: E402

PREFIX = "dummy_"
INDUSTRIES = {"제조업": 0.45, "서비스업": 0.35, "도소매업": 0.20}
# 업종별로 A 성향(G·I·N·P)을 고를 확률. 0.5에서 멀수록 그 업종 경영자가 한쪽으로 치우친다(가상 설정).
A_PROB = {
    "제조업": {"G": 0.55, "I": 0.65, "N": 0.30, "P": 0.35},
    "서비스업": {"G": 0.75, "I": 0.70, "N": 0.65, "P": 0.40},
    "도소매업": {"G": 0.40, "I": 0.25, "N": 0.45, "P": 0.30},
}
DETAIL = {"제조업": ["식품 제조", "정밀부품", "화장품 OEM", "의료기기", "2차전지 소재"],
          "서비스업": ["B2B SaaS", "교육 플랫폼", "마케팅 대행", "헬스케어 앱", "물류 IT"],
          "도소매업": ["온라인 생활용품", "식자재 유통", "패션 편집숍", "수입 주방용품", "반려동물용품"]}


def admin_api(method: str, path: str, body: dict | None = None) -> dict:
    key = settings.SUPABASE_SECRET_KEY
    headers = {"apikey": key, "Content-Type": "application/json"}
    if key.startswith("eyJ"):
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(f"{settings.SUPABASE_URL}/auth/v1/admin/{path}", method=method, headers=headers,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=20) as res:
        return json.loads(res.read() or b"{}")


def clip(x: float, lo: int = 1, hi: int = 5) -> int:
    return max(lo, min(hi, int(round(x))))


def axis_answers(rng: random.Random, lean_a: bool, strength: float) -> list[int]:
    """한 축 6문항. 축 점수 = Σ(x−1)/24×100 이 경계(37.5~62.5)를 벗어날 때까지 다시 뽑는다."""
    while True:
        target = 50 + (1 if lean_a else -1) * strength  # 목표 축 점수
        mean = 1 + target / 100 * 4
        xs = [clip(rng.gauss(mean, 0.75)) for _ in range(6)]
        score = sum(x - 1 for x in xs) / 24 * 100
        if (score >= 62.5) if lean_a else (score <= 37.5):
            return xs


def make_profile(rng: random.Random, industry: str) -> dict:
    """경영자 1명의 성향: 축별 방향과 세기(15~45점 치우침)."""
    return {ax: {"a": rng.random() < p, "strength": rng.uniform(15, 45)} for ax, p in A_PROB[industry].items()}


def drift(rng: random.Random, profile: dict) -> dict:
    """재진단: 대부분 같은 방향, 15% 확률로 한 축이 뒤집힌다(유형 안정성 확인용)."""
    out = {ax: dict(v, strength=max(15, min(45, v["strength"] + rng.uniform(-8, 8)))) for ax, v in profile.items()}
    if rng.random() < 0.15:
        ax = rng.choice(list(out))
        out[ax]["a"] = not out[ax]["a"]
    return out


def make_survey(rng: random.Random, q: dict, i: int, industry: str, company: dict, profile: dict, level: float) -> dict:
    dna = {}
    for k, ax in enumerate(("G", "I", "N", "P")):
        for j, x in enumerate(axis_answers(rng, profile[ax]["a"], profile[ax]["strength"])):
            dna[f"D{k * 6 + j + 1:02d}"] = x
    age = 2026 - company["founded_year"]
    stage_base = 1.6 + min(age, 15) / 15 * 2.4 + rng.gauss(0, 0.5)
    stage = {k: clip(stage_base + rng.gauss(0, 0.7)) for k in ("product", "customer", "revenue", "cash", "operations", "expansion")}
    competence = {}
    for d in "ABCDEFGH":
        dl = level + rng.gauss(0, 0.45)
        for n in range(1, 9):
            competence[f"{d}{n:02d}"] = clip(dl + rng.gauss(0, 0.6))
    items = {it["code"]: it for it in q["plan"]["items"]}

    def pick(code: str, lo: int, hi: int) -> list[str]:
        opts = [o if isinstance(o, str) else o["value"] for o in items[code]["options"]]
        return rng.sample(opts, rng.randint(lo, min(hi, items[code].get("max", hi))))

    sales = company["sales_recent"]
    plan = {
        "P01": pick("P01", 1, 3), "P09": pick("P09", 0, 3), "P05": pick("P05", 1, 3),
        "P10": pick("P10", 1, 3), "P11": pick("P11", 1, 3), "P12": pick("P12", 1, 3),
        "P02": round(sales * rng.uniform(1.1, 2.5), 1), "P03": rng.randint(0, 20),
        "P04": round(rng.uniform(0, 30), 1), "P06": round(rng.uniform(0, 50), 1),
        "P07": rng.choice([o if isinstance(o, str) else o["value"] for o in items["P07"]["options"]]),
        "P08": rng.choice([o if isinstance(o, str) else o["value"] for o in items["P08"]["options"]]),
    }
    return {"company": company | {"name": f"더미기업{i:03d}", "industry": industry,
                                  "industry_detail": rng.choice(DETAIL[industry])},
            "answers": {"dna": dna, "stage": stage, "competence": competence, "plan": plan}}


def make_company(rng: random.Random) -> dict:
    founded = rng.choice(range(1998, 2026))
    age = 2026 - founded
    employees = max(1, int(rng.lognormvariate(1.6 + min(age, 20) * 0.09, 0.7)))
    sales = round(max(0.1, employees * rng.uniform(0.6, 2.2)), 1)
    return {"founded_year": founded, "employees": employees, "sales_recent": sales,
            "sales_prev": round(sales / rng.uniform(0.75, 1.6), 1) if rng.random() < 0.8 else None,
            "operating_margin": round(rng.gauss(4, 9), 1) if rng.random() < 0.7 else None,
            "customer_type": rng.sample(["기업(B2B)", "소비자(B2C)", "공공(B2G)", "해외"], rng.randint(1, 2)),
            "main_channel": "더미 채널"}


def seed(count: int, seed_value: int) -> None:
    rng = random.Random(seed_value)
    q = load_questions()
    store = PostgresStore(settings.POSTGRES_URL_NON_POOLING or settings.POSTGRES_URL)
    now = datetime.now(timezone.utc)
    made = users = 0
    while made < count:
        industry = rng.choices(list(INDUSTRIES), weights=list(INDUSTRIES.values()))[0]
        username = f"{PREFIX}{rng.randrange(16**6):06x}"
        user = admin_api("POST", "users", {
            "email": username_to_email(username), "password": "Dm-" + "%016x" % rng.getrandbits(64), "email_confirm": True,
            "user_metadata": {"name": "더미", "username": username,
                              "consents": {"privacy": "dummy", "storage": "dummy", "analytics": "dummy"}}})
        users += 1
        company = make_company(rng)
        profile = make_profile(rng, industry)
        level = rng.gauss(3.3, 0.6)  # 역량 수준(1~5 척도 평균)
        rounds = 2 if rng.random() < 0.3 and made + 2 <= count else 1
        first = now - timedelta(days=rng.uniform(20, 120))
        for r in range(rounds):
            if r:
                profile, level = drift(rng, profile), level + rng.gauss(0.25, 0.3)
                company = company | {"sales_prev": company["sales_recent"],
                                     "sales_recent": round(company["sales_recent"] * rng.uniform(0.9, 1.5), 1)}
            survey = make_survey(rng, q, made, industry, company, profile, level)
            phase = "full" if rng.random() < 0.75 else "basic"
            result = diagnose_survey(survey, phase)
            completed = min(now, first + timedelta(days=r * rng.uniform(60, 100)))
            store.create(str(user["id"]), {
                "survey": survey, "progress": {"step": 0, "maxStep": 0, "basicDone": True, "phase": phase, "percent": 100},
                "company_name": survey["company"]["name"], "result": result, "phase": phase,
                "status": "full_completed" if phase == "full" else "basic_completed",
                "model_version": result["model_version"], "questions_version": result["questions_version"],
                "completed_at": completed})
            made += 1
        print(f"\r더미 진단 {made}/{count} (회원 {users})", end="", flush=True)
    print()


def clean() -> None:
    url = _clean_url(settings.POSTGRES_URL_NON_POOLING)
    with psycopg.connect(url, autocommit=True) as c:
        ids = [str(r[0]) for r in c.execute(
            "select id from auth.users where raw_user_meta_data->>'username' like %s", (PREFIX + "%",)).fetchall()]
        for uid in ids:
            row = c.execute("select subject_key from private.subject_map where user_id = %s", (uid,)).fetchone()
            if row:
                c.execute("delete from analytics.diagnosis_facts where subject_key = %s", (row[0],))
                c.execute("delete from analytics.funnel_events where subject_key = %s", (row[0],))
            c.execute("delete from public.diagnoses where created_by = %s", (uid,))
    for uid in ids:
        try:
            admin_api("DELETE", f"users/{uid}")
        except urllib.error.HTTPError as e:
            print("삭제 실패", uid, e.code)
    print(f"더미 회원 {len(ids)}명과 그 진단·분석 행을 지웠습니다.")


def main() -> int:
    ap = argparse.ArgumentParser(description="더미 경영자 진단 만들기·지우기")
    ap.add_argument("--count", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20261118, help="난수 시드(같은 값이면 같은 데이터)")
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    if not (settings.SUPABASE_URL and settings.SUPABASE_SECRET_KEY and settings.POSTGRES_URL_NON_POOLING):
        print("api/.env에 SUPABASE_URL, SUPABASE_SECRET_KEY, POSTGRES_URL_NON_POOLING이 필요합니다.")
        return 1
    clean() if args.clean else seed(args.count, args.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
