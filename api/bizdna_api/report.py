"""PDF 보고서 생성 (FR-11 기본형, FR-13 정밀형).

legacy/BizDNA_Integrated/reports.py를 옮겼다. 바뀐 점:
- 이미 계산된 엔진 결과를 받는다(엔진을 다시 돌리지 않음).
- 폰트: BIZDNA_FONT_REGULAR/BOLD 환경변수 → 저장소에 포함한 api/fonts/ 나눔고딕 → Windows 맑은 고딕 → Linux 나눔 순으로 찾는다.
- 색상을 웹 디자인 토큰(docs/design-system.md)에 맞췄다.
- AI 서술은 아직 붙이지 않는다(FR-20, P2).
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
NAVY = colors.HexColor("#0A1628")
BLUE = colors.HexColor("#0071E3")
TEAL = colors.HexColor("#0D838B")
LIGHT = colors.HexColor("#F5F5F7")
CHIP = colors.HexColor("#E8F3FF")
GRAY = colors.HexColor("#86868B")
LINE = colors.HexColor("#E3E6EA")

BUNDLED_FONTS = Path(__file__).resolve().parents[1] / "fonts"  # 나눔고딕(OFL), 배포 서버에도 같이 올라간다
FONT_CANDIDATES = [
    (os.environ.get("BIZDNA_FONT_REGULAR"), os.environ.get("BIZDNA_FONT_BOLD")),
    (str(BUNDLED_FONTS / "NanumGothic-Regular.ttf"), str(BUNDLED_FONTS / "NanumGothic-Bold.ttf")),
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),
    ("/usr/share/fonts/truetype/nanum/NanumSquareR.ttf", "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"),
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    ("/System/Library/Fonts/Supplemental/AppleGothic.ttf", "/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
]
_fonts_ready = False


def _register_fonts() -> None:
    global _fonts_ready
    if _fonts_ready:
        return
    for regular, bold in FONT_CANDIDATES:
        if regular and Path(regular).exists():
            pdfmetrics.registerFont(TTFont("BizKR", regular))
            pdfmetrics.registerFont(TTFont("BizKRB", bold if bold and Path(bold).exists() else regular))
            _fonts_ready = True
            return
    raise RuntimeError("한글 폰트를 찾지 못했습니다. BIZDNA_FONT_REGULAR 환경변수로 TTF 경로를 지정하세요.")


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontName="BizKRB", fontSize=24, leading=34, textColor=INK, spaceAfter=6),
        "kicker": ParagraphStyle("kicker", fontName="BizKRB", fontSize=9, leading=14, textColor=BLUE, spaceAfter=14),
        "h": ParagraphStyle("h", fontName="BizKRB", fontSize=15, leading=23, textColor=INK, spaceBefore=4, spaceAfter=12),
        "sub": ParagraphStyle("sub", fontName="BizKRB", fontSize=10.5, leading=17, textColor=BLUE, spaceBefore=12, spaceAfter=7),
        "body": ParagraphStyle("body", fontName="BizKR", fontSize=9.2, leading=16, textColor=INK, spaceAfter=8),
        "tiny": ParagraphStyle("tiny", fontName="BizKR", fontSize=7.7, leading=12, textColor=GRAY, spaceAfter=6),
        "cell": ParagraphStyle("cell", fontName="BizKR", fontSize=8.2, leading=12, textColor=INK),
        "th": ParagraphStyle("th", fontName="BizKRB", fontSize=8.2, leading=12, textColor=colors.white),
    }


class Bars(Flowable):
    """가로 막대그래프. 70점 이상은 청록, 그 외 파랑."""

    def __init__(self, items: list[tuple[str, float | None]], width: float = 465, row: float = 26):
        super().__init__()
        self.items, self.width, self.row = items, width, row
        self.height = len(items) * row + 10

    def draw(self) -> None:
        c = self.canv
        track = self.width - 220
        for i, (label, val) in enumerate(self.items):
            y = self.height - 20 - i * self.row
            c.setFont("BizKR", 8.2)
            c.setFillColor(INK)
            c.drawString(0, y, label[:18])
            c.setFillColor(LIGHT)
            c.roundRect(172, y - 2, track, 10, 5, fill=1, stroke=0)
            if val is None:
                c.setFillColor(GRAY)
                c.drawRightString(self.width, y, "결측")
                continue
            c.setFillColor(TEAL if val >= 70 else BLUE)
            c.roundRect(172, y - 2, max(10, track * max(0, min(100, val)) / 100), 10, 5, fill=1, stroke=0)
            c.setFillColor(INK)
            c.drawRightString(self.width, y, f"{val:.1f}")


def _footer(c, doc) -> None:
    w, _ = A4
    c.setStrokeColor(LINE)
    c.line(19 * mm, 17 * mm, w - 19 * mm, 17 * mm)
    c.setFillColor(GRAY)
    c.setFont("BizKR", 7)
    c.drawString(19 * mm, 12 * mm, "Biz-DNA (가칭) | 중소기업 경영진단 보고서 · 시범모형")
    c.drawRightString(w - 19 * mm, 12 * mm, f"{doc.page:02d}")


def build_report(result: dict[str, Any], mode: str = "basic") -> bytes:
    if mode not in ("basic", "advanced"):
        raise ValueError("mode: basic 또는 advanced")
    if result.get("competence") is None:
        raise ValueError("보고서는 정밀진단(경영역량)까지 마친 결과로만 만들 수 있습니다.")
    _register_fonts()
    st = _styles()

    def p(text: Any, kind: str = "body") -> Paragraph:
        return Paragraph(escape(str(text)).replace("\n", "<br/>"), st[kind])

    def table(rows: list[list[Any]], widths: list[float] | None = None) -> Table:
        t = Table([[p(x, "th" if i == 0 else "cell") for x in row] for i, row in enumerate(rows)],
                  colWidths=widths, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, -1), (-1, -1), .4, LINE),
        ]))
        return t

    r = result
    company = r.get("company") or {}
    name = company.get("name") or "기업명 미입력"
    comp = r["competence"]
    domains = comp["domains"]
    names = comp["names"]
    scored = {k: v for k, v in domains.items() if v is not None}
    ordered = sorted(scored, key=scored.get)
    tops = r["top_recommended"] or []
    risks = r["risks"]
    dna = r["dna"]
    stage = r["stage"] or {}
    type_label = f'{dna["type"]} · {dna["name"]}' if dna.get("name") else f'{dna["type"]} (일부 축 판정 불가)'
    stage_label = f'{stage["code"]} · {stage["name"]}' if stage.get("code") else "판정 불가(문항 미응답)"
    grade = comp["grade"]

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=19 * mm, rightMargin=19 * mm, topMargin=22 * mm,
                            bottomMargin=22 * mm, title=f"{name} Biz-DNA 진단보고서", author="Biz-DNA")
    s: list[Any] = []

    def new(title: str) -> None:
        s.append(PageBreak())
        s.append(p(title, "h"))

    s.append(p("BIZ-DNA DIAGNOSIS REPORT", "kicker"))
    s.append(p("기업 경영진단 보고서", "title"))
    s.append(p("기본형 · 핵심 진단 및 전략" if mode == "basic" else "정밀형 · 경영역량 및 성장전략 심층분석", "sub"))
    s.append(Spacer(1, 6))
    s.append(table([
        ["진단 항목", "분석 결과"],
        ["기업명", name],
        ["업종", " / ".join(x for x in [company.get("industry"), company.get("industry_detail")] if x) or "미입력"],
        ["DNA 유형", type_label],
        ["성장단계", stage_label],
        ["경영역량", f'{comp["total"]:.2f} / 100점 · {grade["grade"]}등급 ({grade["name"]})'],
        ["우선 개선영역", " / ".join(names[x] for x in ordered[:2])],
        ["진단일", datetime.date.today().isoformat()],
    ], widths=[48 * mm, 122 * mm]))
    s.append(p("경영진단 핵심 메시지", "sub"))
    strongest = max(scored, key=scored.get)
    s.append(p(f'{name}은(는) {dna.get("name") or dna["type"]} 성향이며 {stage.get("name") or "성장단계 미판정"} 상태로 진단되었습니다. '
               f'상대적 강점은 {names[strongest]}, 최우선 보완영역은 {names[ordered[0]]}입니다. '
               f'이 결과는 응답에 근거한 판단이며 실제 경영성과를 보증하지 않습니다.'))
    s.append(p("성장전략 상위 3개", "sub"))
    s.append(table([["순위", "전략명", "우선순위 점수"]] + [[str(i), t["name"], f'{t["score"]:.2f}'] for i, t in enumerate(tops[:3], 1)],
                   widths=[20 * mm, 115 * mm, 35 * mm]))
    s.append(p("진단결과는 자기보고 응답 기반 시범모형이며, 업종별 표준화·외부 증빙·전문가 검증이 완료되지 않았습니다.", "tiny"))

    new("01 | 기업 DNA 및 성장단계")
    s.append(table([["성향축", "점수", "판정", "유의"]] + [
        [k, "결측" if v["score"] is None else f'{v["score"]:.1f}', v.get("tendency") or "판정 불가",
         "경계 성향 · 재확인 권장" if v.get("boundary") else ("응답 부족" if v.get("low_reliability") else "")]
        for k, v in dna["axes"].items()], widths=[45 * mm, 25 * mm, 45 * mm, 55 * mm]))
    if dna.get("profile"):
        s.append(p("유형 특성", "sub"))
        s.append(p(f'{dna["type"]} {dna["name"]}: 주요 특성은 {dna["profile"]["traits"]}이며, 기본 성장전략은 {dna["profile"]["strategy"]}입니다. 유형은 우열이 아니며 재진단 때 바뀔 수 있습니다.'))
    s.append(p("성장단계 판정", "sub"))
    if stage.get("code"):
        s.append(p(f'가중지수 {stage["weighted_index"]:.2f}(1~5), 최종 판정 {stage["code"]} {stage["name"]}. 핵심 과제는 {stage["task"]}입니다.'))
        for g in stage["gates_applied"]:
            s.append(p(f'• 필수 통과조건 {g["id"]}: {g["reason"]}'))
        if not stage["gates_applied"]:
            s.append(p("필수 통과조건에 따른 하향 조정은 없었습니다."))
    else:
        s.append(p("성장단계 문항에 모두 응답하지 않아 단계를 판정하지 않았습니다."))

    new("02 | 8대 경영역량")
    s.append(Bars([(names[k], v) for k, v in domains.items()]))
    s.append(table([["진단영역", "점수", "진단해석"]] + [
        [names[k], "결측" if v is None else f"{v:.2f}",
         "응답 없음" if v is None else "우선개선 검토" if v < 55 else "선택적 보완" if v < 70 else "강점 유지·활용"]
        for k, v in domains.items()], widths=[75 * mm, 29 * mm, 66 * mm]))
    if comp["missing"]:
        s.append(p(f'미응답 {len(comp["missing"])}문항은 0점으로 처리하지 않고 결측으로 제외했습니다.', "tiny"))
    s.append(p("점수는 업종 내 백분위가 아니라 설문응답을 100점으로 환산한 값입니다.", "tiny"))

    new("03 | 핵심 경영문제 및 성장제약")
    for i, k in enumerate(ordered[:3], 1):
        s.append(p(f"{i}. {names[k]} · {domains[k]:.1f}점", "sub"))
        s.append(p(f"8대 경영역량 중 {i}번째로 낮은 영역입니다. 실제 병목 여부는 증빙자료와 담당자 인터뷰로 확인하고, 성장목표에 필요한 최소 역량수준을 정해야 합니다."))
    s.append(p("성장장애·위험요인", "sub"))
    if risks:
        for x in risks:
            s.append(p(f"• {x}"))
    else:
        s.append(p("응답에서 주요 위험요인이 선택되지 않았습니다. 위험이 없다는 의미는 아닙니다."))

    new("04 | 성장전략 추천 및 실행과제")
    for i, t in enumerate(tops[:3], 1):
        s.append(p(f'{i}순위 · {t["name"]} ({t["code"]}, {t["score"]:.1f}점)', "sub"))
        s.append(p("실행과제: " + " / ".join(t["actions"])))
        f = t["factors"]
        basis = f'선정근거: 적합성 {f["fit"]:.0f} · 시급성 {f["urgency"]:.0f} · 기대효과 {f["impact"]:.0f} · 실행가능성 {f["feasibility"]:.0f}'
        if t["applied_rules"]:
            basis += " · 적용 규칙 " + ", ".join(t["applied_rules"])
        s.append(p(basis, "tiny"))
    deferred = [x for x in r["strategies"] if x["status"] == "deferred"]
    if deferred:
        s.append(p("선행조건 미충족으로 보류한 전략", "sub"))
        for t in deferred:
            s.append(p(f'• {t["name"]}({t["code"]}): {" / ".join(t["reasons"])}'))

    new("05 | 성장 실행 로드맵 및 관리지표")
    s.append(table([["시기", "우선전략", "실행내용"]] + [[period, t["name"], " / ".join(t["actions"])] for period, t in zip(["0~3개월", "3~6개월", "6~12개월"], tops[:3])],
                   widths=[27 * mm, 55 * mm, 88 * mm]))
    s.append(p("전략별 핵심성과지표(KPI)", "sub"))
    s.append(table([["전략", "KPI 1", "KPI 2"]] + [[t["name"], *t["kpis"]] for t in tops[:3]], widths=[70 * mm, 50 * mm, 50 * mm]))
    s.append(p("권장 일정과 KPI는 기본 템플릿입니다. 실제 목표치는 기초값·예산·담당조직을 확인한 뒤 정합니다.", "tiny"))

    if mode == "advanced":
        new("06 | 강점과 취약점의 불균형")
        strong3 = sorted(scored, key=scored.get, reverse=True)[:3]
        s.append(table([["상대적 강점", "점수"]] + [[names[k], f"{domains[k]:.1f}"] for k in strong3], widths=[115 * mm, 55 * mm]))
        s.append(p(f"최상위 영역과 최하위 영역의 점수 차이는 {domains[strong3[0]] - domains[ordered[0]]:.1f}점입니다. 강점이 충분해도 취약영역이 확장의 제약이 될 수 있어 개선 우선순위를 조정해야 합니다."))
        new("07 | 전략별 선정근거")
        for t in tops[:5]:
            s.append(p(f'{t["code"]} · {t["name"]}', "sub"))
            s.append(p(f'추천점수 {t["score"]:.2f}점. 연계 목표: {", ".join(t["matched_goals"]) or "없음"}. 산정요소: ' + ", ".join(f"{k} {v:.1f}" for k, v in t["factors"].items()) + "."))
            if t["reasons"]:
                s.append(p("규칙 조정: " + " / ".join(t["reasons"])))
        new("08 | 90일 실행계획")
        s.append(table([["기간", "실행내용", "검증자료"]] + [[f"{i * 30 + 1}~{(i + 1) * 30}일", " / ".join(t["actions"]), "담당자·완료증빙·KPI 기초값"] for i, t in enumerate(tops[:3])],
                       widths=[29 * mm, 90 * mm, 51 * mm]))
        new("09 | 1~3년 로드맵과 재진단")
        s.append(table([["시기", "전략목표", "필수 검증조건"],
                        ["1차년도", "핵심 병목 해소 및 경영기반 정비", "재무·고객·운영 지표 기준값 확정"],
                        ["2차년도", "검증된 시장·제품 전략의 선택적 확장", "수익성·고객유지·공급역량 검증"],
                        ["3차년도", "조직·자금 여건을 고려한 성장 고도화", "투자성과·조직생산성 평가"]], widths=[28 * mm, 75 * mm, 67 * mm]))
        s.append(Spacer(1, 10))
        s.append(table([["주기", "관리내용"], ["3개월", "실행과제 완료율·선행조건 확인"], ["6개월", "8대 경영역량 부분 재진단"], ["12개월", "DNA 성향·성장단계·전략 적합성 재평가"]], widths=[40 * mm, 130 * mm]))

    s.append(p("진단결과 활용 시 유의사항", "sub"))
    for lim in r["limitations"]:
        s.append(p("• " + lim, "tiny"))
    s.append(p(f'모형 {r["model_version"]} · 문항 {r.get("questions_version", "-")}', "tiny"))
    doc.build(s, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
