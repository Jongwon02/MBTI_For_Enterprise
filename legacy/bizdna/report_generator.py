"""Biz-DNA automatic Korean PDF reports. Usage: python report_generator.py input.json output.pdf"""
import sys,json,os
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from engine import diagnose,DOMAINS
FONT='/usr/share/fonts/truetype/nanum/NanumSquareR.ttf'
BOLD='/usr/share/fonts/truetype/nanum/NanumSquareB.ttf'
if not os.path.exists(FONT):
 import subprocess
 FONT=subprocess.check_output(['fc-match','-f','%{file}','NanumSquare']).decode()
 BOLD=FONT
pdfmetrics.registerFont(TTFont('KR',FONT));pdfmetrics.registerFont(TTFont('KRB',BOLD))
NAVY=colors.HexColor('#18354F');TEAL=colors.HexColor('#117F88');LIGHT=colors.HexColor('#EEF4F7')
styles={
 'title':ParagraphStyle('title',fontName='KRB',fontSize=20,leading=29,textColor=NAVY,spaceAfter=13),
 'heading':ParagraphStyle('heading',fontName='KRB',fontSize=13,leading=20,textColor=NAVY,spaceBefore=15,spaceAfter=9),
 'body':ParagraphStyle('body',fontName='KR',fontSize=9,leading=16,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='KR',fontSize=8,leading=13),
 'cell':ParagraphStyle('cell',fontName='KR',fontSize=8.3,leading=13),
 'cellhead':ParagraphStyle('cellhead',fontName='KRB',fontSize=8.5,leading=13,textColor=colors.white),
}
TYPE_NAMES={'GICO':'기술중심 성장형','GINO':'창업자 주도 혁신형','GINP':'혁신시장 개척형','GECP':'체계적 규모성장형','SECP':'안정경영 최적화형'}
STRATEGY_ACTIONS={
 'ST01':['목표고객 인터뷰와 유료구매 검증','사업모델 가설·가격정책 재설계'],
 'ST02':['고객 사용성·이탈원인 분석','제품개선 우선순위 수립'],
 'ST03':['목표고객군별 채널성과 비교','수익성 확인 후 신규판로 단계적 확대'],
 'ST04':['고객획득비용 및 전환율 측정','고객군별 마케팅 메시지 최적화'],
 'ST05':['핵심제품 개선 로드맵 수립','기술·제품 투자성과 검증'],
 'ST06':['제품별 원가·공헌이익 분석','가격·제품구성·고정비 개선'],
 'ST07':['13주 현금흐름 및 12개월 자금계획 작성','운전자금·차입상환 일정 점검'],
 'ST08':['핵심업무 책임자 지정 및 권한위임','인력충원·직무표준화 계획 수립'],
 'ST09':['공급·고객지원 병목 프로세스 측정','품질·납기·처리시간 개선'],
 'ST10':['반복업무 자동화 후보 선정','데이터 수집·접근권한 체계 정비'],
 'ST11':['투자자금 사용계획·성장가정 검증','투자유치 자료 및 재무모델 정비'],
 'ST12':['신사업 고객·수익성 소규모 검증','사업전환 단계별 중단조건 설정']}
RISK_ACTIONS={'현금흐름 위험':'현금유출 관리 및 단기 유동성 확보를 최우선으로 검토','시장검증 미완료':'확장투자 이전에 유료고객과 반복구매를 확인','단위경제성 악화':'판매량 확대 이전에 제품별 공헌이익 개선','창업자 의존':'업무 권한위임과 핵심인력 확보','공급능력 부족':'판로확대 이전에 생산·서비스 처리능력 보완','성장자금 부족':'투자집행 단계화 및 조달가능성 검토','서비스 운영부담':'고객지원 프로세스 표준화와 처리시간 관리'}
def P(x,kind='body'): return Paragraph(escape(str(x)).replace('\n','<br/>'),styles[kind])
def make_table(rows,widths=None):
 t=Table([[P(v,'cellhead' if i==0 else 'cell') for v in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CBD8DF'))]))
 return t
def footer(c,d):
 c.setFont('KR',8);c.setFillColor(colors.HexColor('#64748B'));c.drawString(20*mm,13*mm,'Biz-DNA 2.0 | 자동 경영진단 보고서 · 시범모형');c.drawRightString(190*mm,13*mm,str(d.page))
def generate(payload,out):
 r=diagnose(payload);company=r['company'];name=company.get('name','미상 기업');ds=r['competence']['domains'];ranked=sorted(ds.items(),key=lambda p:p[1]);strong=sorted(ds.items(),key=lambda p:-p[1])[:2];top=r['top_recommended'][:3];risks=r['risks']
 doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=19*mm,leftMargin=19*mm,topMargin=21*mm,bottomMargin=22*mm)
 s=[]
 s +=[P('Biz-DNA 기업 경영진단 보고서','title'),P(f'진단기업: {name}  |  업종: {company.get("industry","미입력")}'),P('본 보고서는 설문응답 기반의 시범 알고리즘으로 자동 생성되었습니다. 전문가 확인 및 객관적 증빙검토 전에는 투자·금융 의사결정의 단독 근거로 사용하지 마십시오.','small'),Spacer(1,7*mm)]
 s +=[P('01. 종합진단 요약','heading'),make_table([['진단항목','진단결과'],['기업 DNA',r['dna']['type']+' · '+TYPE_NAMES.get(r['dna']['type'],'기업 경영유형')],['성장단계',r['stage']['code']+' · '+r['stage']['name']],['경영역량 종합점수',f'{r["competence"]["total"]:.2f} / 100'],['상위 역량',', '.join(DOMAINS[k][0] for k,v in strong)],['개선 우선영역',', '.join(DOMAINS[k][0] for k,v in ranked[:2])]],widths=[55*mm,115*mm])]
 s +=[P('종합 해석','heading'),P(f'{name}의 경영성향은 {r["dna"]["type"]} 유형이며, 현재 성장단계는 {r["stage"]["name"]}로 판정되었습니다. 상대적 강점은 {" 및 ".join(DOMAINS[k][0] for k,v in strong)}이며, 개선 필요영역은 {" 및 ".join(DOMAINS[k][0] for k,v in ranked[:2])}입니다. 이는 입력된 설문응답에 따른 비교이며 외부 기업 평균과의 비교가 아닙니다.')]
 s +=[P('02. 기업 DNA 성향','heading'),make_table([['진단축','점수','분류','경계여부']]+[[k,str(v['score']),v['letter'],'경계' if v['boundary'] else '명확'] for k,v in r['dna']['axes'].items()],widths=[53*mm,31*mm,37*mm,49*mm])]
 s +=[P('03. 8대 경영역량','heading'),make_table([['영역','점수','진단의견']]+[[DOMAINS[k][0],f'{v:.2f}',('우선 개선검토' if v<55 else '선택적 보완' if v<70 else '강점 유지·활용')] for k,v in ds.items()],widths=[76*mm,31*mm,63*mm])]
 s +=[PageBreak(),P('04. 핵심 경영위험 및 성장제약','heading')]
 if risks:
  for i,risk in enumerate(risks,1):s.append(P(f'{i}. {risk} — {RISK_ACTIONS.get(risk,"추가 확인 필요")}'))
 else:s.append(P('사전 정의된 주요 위험 플래그는 확인되지 않았습니다. 위험 부재를 의미하지 않으며 객관적 자료 검증이 필요합니다.'))
 s +=[P('05. 맞춤형 성장전략 추천','heading'),P('전략점수는 적합성·시급성·기대효과·실행가능성의 규칙기반 우선순위 지표이며 실제 성과확률이 아닙니다.','small')]
 for i,t in enumerate(top,1):
  s +=[P(f'{i}순위 · {t["name"]} ({t["code"]}, {t["score"]:.2f}점)','heading'),P('주요 실행과제: '+' / '.join(STRATEGY_ACTIONS.get(t['code'],[]))),P(f'추천 근거: 적합성 {t["factors"]["fit"]:.0f}, 개선시급성 {t["factors"]["urgency"]:.0f}, 기대효과 {t["factors"]["impact"]:.0f}, 실행가능성 {t["factors"]["feasibility"]:.0f}점.')]
 deferred=[x for x in r['strategies'] if x['status']=='deferred']
 if deferred:s +=[P('06. 선행조건 미충족으로 보류된 전략','heading'),P(', '.join(f'{x["name"]} ({x["code"]})' for x in deferred)),P('보류된 전략은 현금흐름·시장검증·공급능력 등 선행조건이 충족된 후 재평가해야 합니다.')]
 s +=[PageBreak(),P('07. 실행 로드맵 및 성과관리','heading')]
 phases=[('0~3개월','위험 및 병목 확인',top[0] if top else None),('3~6개월','운영체계 개선',top[1] if len(top)>1 else None),('6~12개월','성장과제 실행',top[2] if len(top)>2 else None)]
 s.append(make_table([['기간','추진방향','실행과제']]+[[a,b,' / '.join(STRATEGY_ACTIONS.get(t['code'],[])) if t else '진단결과 확인 후 수립'] for a,b,t in phases],widths=[27*mm,41*mm,102*mm]))
 s +=[P('성과관리 지표(권장)','heading'),P('공통 KPI: 월별 매출액, 매출총이익률, 영업현금흐름, 고객유지율, 핵심과제 완료율. 업종에 따라 생산성·고객획득비용·반복매출 등의 지표를 추가합니다.'),P('재진단 및 검증','heading'),P('3개월 단위 실행현황 점검, 6개월 핵심역량 재진단, 12개월 성과·전략 적합성 재평가를 권장합니다. 모든 전략 권고는 실제 투자여력과 시장환경을 확인한 후 확정해야 합니다.'),P('진단의 한계','heading')]
 for lim in r['limitations']:s.append(P('• '+lim,'small'))
 s.append(P('생성방식: Biz-DNA 1.0 결정론적 진단엔진 + 규칙기반 서술 템플릿. 외부 생성형 AI를 호출하지 않으며, 응답에 없는 사실이나 재무수치를 임의로 작성하지 않습니다.','small'))
 doc.build(s,onFirstPage=footer,onLaterPages=footer)
 return r
if __name__=='__main__':
 if len(sys.argv)!=3:raise SystemExit('사용법: python report_generator.py input.json output.pdf')
 with open(sys.argv[1],encoding='utf-8') as f:payload=json.load(f)
 generate(payload,sys.argv[2]);print(sys.argv[2])
