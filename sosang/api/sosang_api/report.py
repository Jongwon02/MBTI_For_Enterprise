"""소상공인 기본형 PDF 보고서 (sosang/CLAUDE.md 14장, 5~6쪽).

중소경영 api/bizdna_api/report.py의 구성(폰트 탐색, 표·막대, 꼬리말)을 복사해 고쳤다.
엔진 결과만 받아 그대로 옮긴다(엔진을 다시 돌리거나 수치를 새로 만들지 않는다). 색은 웹과 같은 초록(#17733b).
"""
from __future__ import annotations

import datetime
import os
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

INK = colors.HexColor("#1D1D1F")
DEEP = colors.HexColor("#0B2416")
ACCENT = colors.HexColor("#17733B")
ACCENT_DEEP = colors.HexColor("#0E4D27")
SECOND = colors.HexColor("#B45309")  # 보완 영역(웹의 주의 색)
LIGHT = colors.HexColor("#F5F5F7")
CHIP = colors.HexColor("#E7F4EC")
GRAY = colors.HexColor("#86868B")
LINE = colors.HexColor("#E3E6EA")
WARN_BG = colors.HexColor("#FFF7ED")

BUNDLED_FONTS = Path(__file__).resolve().parents[1] / "fonts"
FONT_CANDIDATES = [
    (os.environ.get("SOSANG_FONT_REGULAR"), os.environ.get("SOSANG_FONT_BOLD")),
    (str(BUNDLED_FONTS / "NanumGothic-Regular.ttf"), str(BUNDLED_FONTS / "NanumGothic-Bold.ttf")),
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),
]
_fonts_ready = False


def _register_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    for regular, bold in FONT_CANDIDATES:
        if regular and Path(regular).exists():
            pdfmetrics.registerFont(TTFont("SosangKR", regular))
            pdfmetrics.registerFont(TTFont("SosangKRB", bold if bold and Path(bold).exists() else regular))
            _fonts_ready = True
            return
    raise RuntimeError("한글 폰트를 찾지 못했습니다. SOSANG_FONT_REGULAR 환경변수로 TTF 경로를 지정하세요.")


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontName="SosangKRB", fontSize=24, leading=34, textColor=INK, spaceAfter=6),
        "kicker": ParagraphStyle("kicker", fontName="SosangKRB", fontSize=9, leading=14, textColor=ACCENT, spaceAfter=14),
        "h": ParagraphStyle("h", fontName="SosangKRB", fontSize=15, leading=23, textColor=INK, spaceBefore=4, spaceAfter=12),
        "sub": ParagraphStyle("sub", fontName="SosangKRB", fontSize=10.5, leading=17, textColor=ACCENT, spaceBefore=12, spaceAfter=7),
        "body": ParagraphStyle("body", fontName="SosangKR", fontSize=9.2, leading=16, textColor=INK, spaceAfter=8),
        "tiny": ParagraphStyle("tiny", fontName="SosangKR", fontSize=7.7, leading=12, textColor=GRAY, spaceAfter=6),
        "cell": ParagraphStyle("cell", fontName="SosangKR", fontSize=8.2, leading=12, textColor=INK),
        "th": ParagraphStyle("th", fontName="SosangKRB", fontSize=8.2, leading=12, textColor=colors.white),
        "code": ParagraphStyle("code", fontName="SosangKRB", fontSize=44, leading=52, textColor=ACCENT),
    }


class Bars(Flowable):
    """가로 막대그래프(0~100). 강점은 초록, 보완 영역은 주황, 그 외 짙은 초록."""

    def __init__(self, items: list[tuple[str, float | None, str]], width: float = 465, row: float = 26):
        super().__init__()
        self.items, self.width, self.row = items, width, row
        self.height = len(items) * row + 10

    def draw(self) -> None:
        c = self.canv
        track = self.width - 220
        for i, (label, val, tone) in enumerate(self.items):
            y = self.height - 20 - i * self.row
            c.setFont("SosangKR", 8.2)
            c.setFillColor(INK)
            c.drawString(0, y, label[:18])
            c.setFillColor(LIGHT)
            c.roundRect(172, y - 2, track, 10, 5, fill=1, stroke=0)
            if val is None:
                c.setFillColor(GRAY)
                c.drawRightString(self.width, y, "결측")
                continue
            c.setFillColor({"strong": ACCENT, "weak": SECOND}.get(tone, ACCENT_DEEP))
            c.roundRect(172, y - 2, max(10, track * max(0, min(100, val)) / 100), 10, 5, fill=1, stroke=0)
            c.setFillColor(INK)
            c.drawRightString(self.width, y, f"{val:.1f}")


def _footer(c, doc) -> None:
    w, _ = A4
    c.setStrokeColor(LINE)
    c.line(19 * mm, 17 * mm, w - 19 * mm, 17 * mm)
    c.setFillColor(GRAY)
    c.setFont("SosangKR", 7)
    c.drawString(19 * mm, 12 * mm, "Biz-DNA 소상공인 경영진단 (가칭) | 기본형 보고서 · 시범모형")
    c.drawRightString(w - 19 * mm, 12 * mm, f"{doc.page:02d}")


def _table(rows: list[list[Any]], widths: list[float], st: dict[str, ParagraphStyle], head: bool = True) -> Table:
    data = []
    for i, row in enumerate(rows):
        style = st["th"] if head and i == 0 else st["cell"]
        data.append([Paragraph(escape(str(v)), style) for v in row])
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.4, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1 if head else 0), (-1, -1), [colors.white, LIGHT]),
    ]
    if head:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), DEEP))
    t.setStyle(TableStyle(cmds))
    return t


def _won(v: float | None) -> str:
    return "-" if v is None else f"{v:,.0f}만원"


def _pct(v: float | None) -> str:
    return "계산 불가" if v is None else f"{v:.1f}%"


def build_report(r: dict[str, Any]) -> bytes:
    _register_fonts()
    st = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=19 * mm, rightMargin=19 * mm, topMargin=20 * mm,
                            bottomMargin=24 * mm, title=f"소상공인 경영진단 보고서 - {r['store']['name']}",
                            author="Biz-DNA 소상공인 경영진단 (가칭)")
    store, dna, comp, fin, strat = r["store"], r["dna"], r["competence"], r["finance"], r["strategies"]
    areas = {a["code"]: a for a in comp["areas"]}
    s: list[Any] = []
    P = lambda text, style="body": s.append(Paragraph(text, st[style]))  # noqa: E731

    # 1. 표지·점포현황
    P("SMALL BUSINESS MANAGEMENT DIAGNOSIS", "kicker")
    P(f"{escape(store['name'])} 경영진단 보고서", "title")
    P(f"기본형 · 작성일 {datetime.date.today():%Y-%m-%d}", "tiny")
    s.append(Spacer(1, 10))
    P("1. 점포 현황", "h")
    s.append(_table([
        ["항목", "내용"],
        ["업종", f"{store['sector_name']}" + (f" · {store['sub_industry']}" if store.get("sub_industry") else "")],
        ["우선 경영목표", store["goal_name"]],
        ["월 매출", _won(fin["monthly_sales"])],
        ["월 비용 합계", _won(fin["total_cost"])],
        ["성장단계", f"{r['stage']['label']} ({r['stage']['reason']})"],
        ["진단 신뢰도", f"{r['confidence']['level']} · {r['confidence']['note']}"],
    ], [120, 352], st))
    s.append(Spacer(1, 14))
    P("이 보고서를 읽는 법", "sub")
    P("점주가 직접 입력한 응답과 매출·비용으로 계산한 예비진단입니다. 숫자는 점주 자기평가이며, "
      "카드매출·상권 자료로 검증한 값이 아닙니다. " + escape(r["notices"]["model"]))
    s.append(PageBreak())

    # 2. DNA 유형
    P("2. 우리 가게 경영유형 (DNA)", "h")
    if dna["code"]:
        P(" ".join(dna["code"]), "code")
        P(f"<b>{escape(dna['name'])}</b> · 대표 전략방향 {escape(dna['strategy'])}")
    else:
        P("일부 축의 응답이 없어 유형을 판정하지 못했습니다.")
    rows = [["축", "점수", "성향", "비고"]]
    for a in dna["axes"]:
        note = "경계(40~60점): 잠정 판정" if a["boundary"] else ""
        rows.append([a["name"], "-" if a["score"] is None else f"{a['score']:.1f}", a["lean"] or "판정 불가", note])
    s.append(_table(rows, [110, 70, 150, 142], st))
    P("점수가 높을수록 성장확대·차별화·신규고객·체계적 관리 쪽, 낮을수록 안정생계·가격효율·단골고객·점주 직접운영 쪽입니다. "
      "유형은 우열이 아니라 운영 성향입니다.", "tiny")
    s.append(PageBreak())

    # 3. 8대 역량
    P("3. 종합점수와 8대 경영역량", "h")
    if comp["total"] is not None:
        P(f"종합점수 <b>{comp['total']:.2f}점</b> · {comp['grade']['grade']}등급 ({escape(comp['grade']['name'])}) "
          f"· {escape(store['sector_name'])} 가중치 적용")
    strong, weak = set(comp["strengths"]), set(comp["weaknesses"])
    s.append(Bars([(f"{a['code']}. {a['name']}", a["score"], "strong" if a["code"] in strong else "weak" if a["code"] in weak else "")
                   for a in comp["areas"]]))
    s.append(Spacer(1, 8))
    P("강점 영역: " + ", ".join(areas[c]["name"] for c in comp["strengths"]) +
      " · 보완 영역: " + ", ".join(areas[c]["name"] for c in comp["weaknesses"]))
    if comp["special_areas"]:
        P("업종별 심화진단을 답한 영역(" + ", ".join(areas[c]["name"] for c in comp["special_areas"]) +
          ")은 공통 65% + 심화 35%로 계산했습니다.", "tiny")
    if comp["missing_ratio"]:
        P(f"미응답 문항 비율 {comp['missing_ratio'] * 100:.1f}%. 미응답은 0점이 아니라 빈칸으로 보고 제외했습니다.", "tiny")
    s.append(PageBreak())

    # 4. 매출·비용과 위험
    P("4. 매출·비용 구조와 위험 신호", "h")
    s.append(_table([
        ["항목", "금액", "매출 대비"],
        ["월 매출", _won(fin["monthly_sales"]), "100%" if fin["monthly_sales"] else "-"],
        ["원재료·매입비", _won(fin["material_cost"]), _pct(fin["material_ratio_pct"])],
        ["인건비", _won(fin["labor_cost"]), _pct(fin["labor_ratio_pct"])],
        ["임대료", _won(fin["rent"]), _pct(fin["rent_ratio_pct"])],
        ["기타비용", _won(fin["other_cost"]), "-"],
        ["영업잔여액 (매출 - 비용)", _won(fin["operating_residual"]), _pct(fin["residual_margin_pct"])],
    ], [190, 140, 142], st))
    P(escape(r["notices"]["residual"]), "tiny")
    if r.get("sales_growth_pct") is not None:
        P(f"전년 같은 달 대비 매출 변화: {r['sales_growth_pct']:+.1f}% (점주 입력값 기준)")
    if r.get("benchmark"):
        b = r["benchmark"]
        P(f"비교기준 월매출 {_won(b['monthly_sales'])} 대비 {_pct(b['gap_pct'])} · {escape(b['warning'])}", "tiny")
    P("위험 신호", "sub")
    if r["risks"]:
        s.append(_table([["수준", "내용"]] + [["높음" if x["level"] == "high" else "주의", x["text"]] for x in r["risks"]],
                        [60, 412], st))
    else:
        P("입력값 기준으로 해당하는 위험 신호가 없습니다.")
    P("임계값(임대료 20%, 비용 95% 등)은 시범검증 전 임시 기준입니다.", "tiny")
    s.append(PageBreak())

    # 5. 개선전략
    P("5. 먼저 해야 할 개선전략 3가지", "h")
    P(escape(strat["notice"]), "tiny")
    for x in strat["top"]:
        P(f"{x['rank']}순위 · {escape(x['title'])} (우선점수 {x['priority']:.2f})", "sub")
        s.append(_table([
            ["실행과제", x["action"]],
            ["성과지표", x["kpi"]],
            ["선정 근거", x["rationale"]],
        ], [90, 382], st, head=False))
    P("우선점수 = 0.45 × 시급성(100 - 역량 점수) + 0.35 × 적합도(업종·경영목표·위험) + 0.20 × 실행가능성. "
      "점수가 낮은 영역을 그대로 고르지 않고 적자·임대료·목표를 함께 반영합니다.", "tiny")
    s.append(PageBreak())

    # 6. 30·60·90일 실행계획
    P("6. 30·60·90일 실행계획", "h")
    rows = [["전략", "30일", "60일", "90일"]]
    for p in strat["action_plan"]["items"]:
        rows.append([f"{p['rank']}. {p['title']}", p["d30"], p["d60"], p["d90"]])
    s.append(_table(rows, [100, 124, 124, 124], st))
    if strat["action_plan"]["draft"]:
        P("실행계획 문구는 초안입니다. 점포 상황에 맞게 조정해서 쓰세요.", "tiny")
    s.append(Spacer(1, 16))
    P("유의사항", "sub")
    for t in (r["notices"]["model"], r["notices"]["residual"], r["confidence"]["note"],
              "개선활동 전후의 변화가 곧 그 활동의 효과라고 단정할 수는 없습니다."):
        P("· " + escape(t), "tiny")
    v = r["versions"]
    P(f"모형 {v['model']} · 문항 {v['questions']} · 업종분류 {v['industries']}", "tiny")

    doc.build(s, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
