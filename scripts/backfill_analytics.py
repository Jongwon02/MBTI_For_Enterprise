"""기존 완료 회차를 분석 저장소(analytics.*)에 채운다(CLAUDE.md 12.7 백필). 여러 번 돌려도 결과가 같다(멱등).

실행: .venv/Scripts/python scripts/backfill_analytics.py
대상: 통계 활용 동의(consents.kind='analytics', 철회 안 됨)가 있는 회원의 basic_completed·full_completed 회차.
회원별로 completed_at 순서대로 넣으므로 round_no가 완료 순서와 같아진다. 저장된 result를 그대로 쓰고 엔진을 다시 돌리지 않는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from bizdna_api import settings  # noqa: E402
from bizdna_api.store import PostgresStore, _events_for  # noqa: E402


def main() -> int:
    url = settings.POSTGRES_URL_NON_POOLING or settings.POSTGRES_URL
    if not url:
        print("api/.env에 POSTGRES_URL_NON_POOLING이 필요합니다.")
        return 1
    store = PostgresStore(url)
    done = skipped = 0
    with store._conn() as c:
        rows = c.execute(
            "select d.* from public.diagnoses d"
            " where d.status in ('basic_completed', 'full_completed') and d.result is not null"
            " order by d.created_by, d.completed_at").fetchall()
        for row in rows:
            consent = c.execute("select 1 from public.consents where user_id = %s and kind = 'analytics'"
                                " and withdrawn_at is null limit 1", (row["created_by"],)).fetchone()
            if not consent:
                skipped += 1
                continue
            # 수집과 같은 경로(_collect)를 쓴다. started 이벤트도 함께 남긴다(이미 있으면 무시).
            store._collect(c, str(row["created_by"]), row, _events_for(True, row))
            done += 1
    print(f"채움 {done}건, 동의 없음으로 건너뜀 {skipped}건")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
