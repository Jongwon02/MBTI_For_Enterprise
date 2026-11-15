"""Biz-DNA integrated PDF generator: evidence-bound basic and advanced reports."""
import os, json, math, datetime, re
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Flowable
from engine import diagnose, DOMAINS, STRATEGIES

NAVY=colors.HexColor('#17344D'); BLUE=colors.HexColor('#2769A0'); TEAL=colors.HexColor('#0D838B'); LIGHT=colors.HexColor('#EFF5F8'); GRAY=colors.HexColor('#5C6E7A')
font='/usr/share/fonts/truetype/nanum/NanumSquareR.ttf'; bold='/usr/share/fonts/truetype/nanum/NanumSquareB.ttf'
if not os.path.exists(font):
 import subprocess
 font=subprocess.check_output(['fc-match','-f','%{file}','NanumSquare']).decode().strip();bold=font
pdfmetrics.registerFont(TTFont('BizKR',font));pdfmetrics.registerFont(TTFont('BizKRB',bold))
styles={
 'cover':ParagraphStyle('cover',fontName='BizKRB',fontSize=27,leading=39,textColor=NAVY,spaceAfter=18),
 'h':ParagraphStyle('h',fontName='BizKRB',fontSize=15,leading=23,textColor=NAVY,spaceBefore=7,spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='BizKRB',fontSize=10.5,leading=17,textColor=BLUE,spaceBefore=12,spaceAfter=7),
 'body':ParagraphStyle('body',fontName='BizKR',fontSize=9.2,leading=16,spaceAfter=8),
 'tiny':ParagraphStyle('tiny',fontName='BizKR',fontSize=7.7,leading=12,textColor=GRAY,spaceAfter=6),
 'cell':ParagraphStyle('cell',fontName='BizKR',fontSize=8,leading=12),
 'th':ParagraphStyle('th',fontName='BizKRB',fontSize=8,leading=12,textColor=colors.white),
}
TYPE_NAMES={'GINP':'혁신시장 개척형','GINO':'창업자 주도 혁신형','GICP':'혁신시장 심화형','GICO':'기술중심 성장형','GENP':'효율기반 시장확장형','GENO':'기회추구 확장형','GECP':'체계적 규모성장형','GECO':'실행중심 성장형','SINP':'선택적 혁신개척형','SINO':'전문기술 탐색형','SICP':'혁신역량 축적형','SICO':'전문제품 집중형','SENP':'안정기반 시장다변화형','SENO':'기회선택 운영형','SECP':'안정경영 최적화형','SECO':'소규모 내실경영형'}
ACTIONS={
'ST01':['유료고객 인터뷰 10건 이상 계획 수립','사업모델 가설 및 가격정책 검증'],
'ST02':['사용성·이탈원인 분석','핵심제품 개선 우선순위 수립'],
'ST03':['목표 고객군별 채널 수익성 검증','검증된 채널부터 판로 확대'],
'ST04':['고객획득비용과 전환율 측정','고객군별 마케팅 메시지 개선'],
'ST05':['핵심제품 개발 로드맵 수립','제품투자 성과 검증'],
'ST06':['제품별 원가·공헌이익 분석','가격·제품구성·고정비 개선'],
'ST07':['13주 현금흐름표 작성','운전자금·차입금 상환계획 검토'],
'ST08':['업무 책임자·권한위임 기준 수립','핵심인력·직무 표준화'],
'ST09':['공급·고객지원 병목 측정','품질·납기·처리시간 개선'],
'ST10':['자동화 우선업무 선정','데이터 접근권한·보안 관리'],
'ST11':['투자자금 사용계획 검증','재무모델 및 투자자료 정비'],
'ST12':['신사업 고객·수익성 소규모 실증','중단조건·전환일정 설정']}
KPIS={'ST01':['유료고객 수','고객 인터뷰 완료율'],'ST02':['반복구매율','제품 개선 완료율'],'ST03':['신규고객 수','채널별 매출총이익'],'ST04':['고객획득비용','전환율'],'ST05':['신제품 매출비중','개발 마일스톤 달성률'],'ST06':['공헌이익률','영업이익률'],'ST07':['현금보유개월수','현금흐름 예측오차'],'ST08':['대표자 승인업무 비율','핵심직무 충원율'],'ST09':['납기준수율','고객지원 처리시간'],'ST10':['업무자동화율','데이터 오류율'],'ST11':['조달확약금액','투자마일스톤 달성률'],'ST12':['신사업 유료검증 수','실증 단계 완료율']}
RISK={'현금흐름 위험':'확장투자 이전에 현금흐름표와 유동성 확보방안 검토','시장검증 미완료':'유료고객 검증을 우선하고 대규모 판로확대 보류','단위경제성 악화':'제품별 공헌이익을 개선한 후 확장','창업자 의존':'핵심업무의 책임과 권한을 단계적으로 이양','공급능력 부족':'생산·서비스 처리역량 확보 후 신규수주 확대','성장자금 부족':'투자 집행을 단계화하고 조달 가능성 검증','서비스 운영부담':'고객지원 프로세스 표준화 및 처리시간 관리'}

def p(t,kind='body'): return Paragraph(escape(str(t)).replace('\n','<br/>'),styles[kind])
def tbl(rows,widths=None):
 t=Table([[p(x,'th' if i==0 else 'cell') for x in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#D9E3E9'))]))
 return t
class Bars(Flowable):
 def __init__(self,items,width=465,row=27): Flowable.__init__(self);self.items=items;self.width=width;self.height=len(items)*row+12;self.row=row
 def draw(self):
  c=self.canv
  for i,(label,val) in enumerate(self.items):
   y=self.height-22-i*self.row;c.setFont('BizKR',8);c.setFillColor(NAVY);c.drawString(0,y,label[:19]);c.setFillColor(LIGHT);c.roundRect(172,y-2,self.width-217,10,4,fill=1,stroke=0);c.setFillColor(TEAL if val>=70 else BLUE);c.roundRect(172,y-2,(self.width-217)*max(0,min(100,val))/100,10,4,fill=1,stroke=0);c.setFillColor(NAVY);c.drawRightString(self.width,y,f'{val:.1f}')

def foot(c,d):
 w,h=A4;c.setStrokeColor(colors.HexColor('#DCE6EC'));c.line(19*mm,17*mm,w-19*mm,17*mm);c.setFillColor(GRAY);c.setFont('BizKR',7);c.drawString(19*mm,12*mm,'Biz-DNA | 기업진단 자동보고서 · 시범모형');c.drawRightString(w-19*mm,12*mm,f'{d.page:02d}')

def ai_narrative(result,payload):
 """Optional AI narrative. Requires user-provided OPENAI_API_KEY and installed openai.
 Only explanatory text; deterministic scores and decisions remain authoritative.
 """
 if not os.environ.get('OPENAI_API_KEY'):return None
 try:
  from openai import OpenAI
  safe={'company':result['company'],'dna':result['dna'],'competence':result['competence'],'stage':result['stage'],'risks':result['risks'],'top_recommended':result['top_recommended'][:3], 'goals':payload.get('goals',[])}
  response=OpenAI(timeout=35).responses.create(model=os.getenv('BIZDNA_AI_MODEL','gpt-4.1-mini'),instructions='당신은 중소기업 경영진단 분석가. 오직 제공된 JSON 사실만 사용. 점수·유형·우선순위를 수정하지 말 것. 외부 사실, 시장통계, 목표수치, 재무수치를 창작하지 말 것. 미확인 정보는 미확인으로 표시. 한국어로 진단근거와 성장제약, 90일 실행조언을 총 600~900자 작성. 확정적 투자·금융 판단 금지.',input=json.dumps(safe,ensure_ascii=False))
  return response.output_text[:5000]
 except Exception as e:
  return None

def generate(payload,out,mode='basic',use_ai=False):
 if mode not in ('basic','advanced'):raise ValueError('mode must be basic or advanced')
 r=diagnose(payload);company=r['company'];name=company.get('name','기업명 미입력');domains=r['competence']['domains'];ordered=sorted(domains,key=domains.get);tops=r['top_recommended'][:5];risks=r['risks'];code=r['dna']['type'];ai=ai_narrative(r,payload) if use_ai and mode=='advanced' else None
 doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=19*mm,rightMargin=19*mm,topMargin=22*mm,bottomMargin=22*mm,title=f'{name} Biz-DNA {mode} 진단보고서',author='Biz-DNA')
 s=[]
 def heading(t):s.append(p(t,'h'))
 def sub(t):s.append(p(t,'sub'))
 def new(t):s.append(PageBreak());heading(t)
 def note(t):s.append(p(t,'tiny'))
 heading('Biz-DNA 기업 경영진단 보고서')
 s.append(p('기본형 · 핵심 진단 및 전략' if mode=='basic' else 'AI 정밀형 · 경영역량 및 성장전략 심층분석','sub'))
 s.append(tbl([['진단 항목','분석 결과'],['기업명',name],['업종',company.get('industry','미입력')],['DNA 유형',f'{code} · {TYPE_NAMES.get(code,"기업 경영유형")}'],['성장단계',f'{r["stage"]["code"]} · {r["stage"]["name"]}'],['경영역량',f'{r["competence"]["total"]:.2f} / 100점'],['우선 개선영역',' / '.join(DOMAINS[x][0] for x in ordered[:2])]],widths=[48*mm,122*mm]))
 sub('경영진단 핵심 메시지')
 s.append(p(f'{name}은(는) {TYPE_NAMES.get(code,code)} 성향이며 {r["stage"]["name"]}로 판정되었습니다. 강점은 {DOMAINS[max(domains,key=domains.get)][0]}, 최우선 보완영역은 {DOMAINS[ordered[0]][0]}입니다. 현재 응답에 근거한 판단으로 실제 경영성과를 보증하지 않습니다.'))
 sub('성장전략 상위 3개')
 s.append(tbl([['순위','전략명','우선순위 점수']]+[[str(i),t['name'],str(t['score'])] for i,t in enumerate(tops[:3],1)],widths=[20*mm,115*mm,35*mm]))
 note('진단결과는 자기보고 응답 기반 시범모형이며, 업종별 표준화·외부 증빙·전문가 검증이 완료되지 않았습니다.')
 new('01 | 기업 DNA 및 성장단계 진단')
 s.append(tbl([['성향축','점수','유형','판정 유의']]+[[k,f'{v["score"]:.1f}',v['letter'],'경계 성향' if v['boundary'] else ''] for k,v in r['dna']['axes'].items()],widths=[55*mm,30*mm,30*mm,55*mm]))
 sub('성장단계 판정')
 s.append(p(f'성장단계 가중지수 {r["stage"]["weighted_index"]:.2f}점(1~5), 최종 판정 {r["stage"]["code"]} · {r["stage"]["name"]}. '+('필수 통과조건 적용으로 잠정단계가 조정되었습니다.' if r['stage']['gate_adjusted'] else '단계별 필수조건에 따른 하향 조정은 발생하지 않았습니다.')))
 sub('경영성향 해석')
 for axis,detail in r['dna']['axes'].items():s.append(p(f'{axis}: {detail["score"]:.1f}점, 선택유형 {detail["letter"]}.'+(' 성향경계 구간이므로 추가 확인 권장.' if detail['boundary'] else '')))
 new('02 | 8대 경영역량 진단')
 s.append(Bars([(DOMAINS[k][0],v) for k,v in domains.items()]))
 s.append(tbl([['진단영역','점수','진단해석']]+[[DOMAINS[k][0],f'{v:.2f}', '우선개선 검토' if v<55 else '선택적 보완' if v<70 else '강점 유지·활용'] for k,v in domains.items()],widths=[75*mm,29*mm,66*mm]))
 note('점수는 절대적 성과 또는 업종 내 백분위가 아니라 설문응답을 100점으로 환산한 값입니다.')
 new('03 | 핵심 경영문제 및 성장제약')
 for i,k in enumerate(ordered[:3],1):
  sub(f'{i}. {DOMAINS[k][0]} · {domains[k]:.1f}점')
  s.append(p(f'8대 경영역량 중 {i}번째로 낮은 영역입니다. 해당 역량의 실제 병목 여부는 관련 증빙 및 담당자 인터뷰로 확인하고, 성장목표 달성에 필요한 최소 역량을 설정해야 합니다.'))
 sub('위험요인 탐지')
 if risks:
  for x in risks:s.append(p(f'• {x}: {RISK.get(x,"원인 및 실행조건 확인 필요")}'))
 else:s.append(p('입력된 위험 플래그에서 주요 위험요인이 탐지되지 않았습니다. 위험이 존재하지 않는다는 의미는 아닙니다.'))
 new('04 | 성장전략 추천 및 실행과제')
 for i,t in enumerate(tops[:3],1):
  sub(f'{i}순위 · {t["name"]} ({t["code"]}, {t["score"]:.1f}점)')
  s.append(p('실행과제: '+' / '.join(ACTIONS[t['code']])))
  f=t['factors'];note(f'선정근거: 적합성 {f["fit"]:.0f} · 시급성 {f["urgency"]:.0f} · 기대효과 {f["impact"]:.0f} · 실행가능성 {f["feasibility"]:.0f}')
 deferred=[x for x in r['strategies'] if x['status']=='deferred']
 if deferred:
  sub('선행조건 미충족 전략')
  s.append(p(' / '.join(f'{t["name"]}({t["code"]})' for t in deferred)))
 new('05 | 성장 실행 로드맵 및 관리지표')
 s.append(tbl([['시기','우선전략','실행내용']]+[[period,t['name'],' / '.join(ACTIONS[t['code']])] for period,t in zip(['0~3개월','3~6개월','6~12개월'],tops[:3])],widths=[27*mm,55*mm,88*mm]))
 sub('전략별 핵심성과지표(KPI)')
 s.append(tbl([['전략','KPI 1','KPI 2']]+[[t['name'],*KPIS[t['code']]] for t in tops[:3]],widths=[70*mm,50*mm,50*mm]))
 note('권장 일정과 KPI는 기본 템플릿입니다. 실제 목표치는 기초값·예산·담당조직 확인 후 확정해야 합니다.')
 if mode=='advanced':
  new('06 | 기업 성장구조 심층분석')
  sub('기업의 강점과 취약점 간 불균형')
  strongest=sorted(domains,key=domains.get,reverse=True)[:3]
  s.append(tbl([['상대적 강점','점수'],*[[DOMAINS[k][0],f'{domains[k]:.1f}'] for k in strongest]],widths=[115*mm,55*mm]))
  s.append(p(f'상위 영역과 최하위 영역 간 점수 차이는 {domains[strongest[0]]-domains[ordered[0]]:.1f}점입니다. 강점이 충분하더라도 취약영역이 확장 실행의 제약으로 작용할 수 있으므로 개선 우선순위를 조정해야 합니다.'))
  sub('성장전략의 단계적 적용')
  s.append(p('단기에는 재무·고객·운영 측면의 필수조건을 확인하고, 중기에는 검증된 전략을 확대하며, 장기에는 조직·시장·자금 여건을 종합해 투자 규모를 결정합니다.'))
  new('07 | 8대 영역별 세부 개선방향')
  for k in list(domains)[:4]:
   sub(f'{DOMAINS[k][0]} · {domains[k]:.1f}점')
   s.append(p('현 수준의 측정근거를 점검하고, 목표 성장단계에서 요구되는 실행조건을 정의합니다. 관련 문항 중 저득점 응답을 우선 확인하여 구체적 개선과제를 수립합니다.'))
  new('08 | 8대 영역별 세부 개선방향 (계속)')
  for k in list(domains)[4:]:
   sub(f'{DOMAINS[k][0]} · {domains[k]:.1f}점')
   s.append(p('담당조직·업무절차·성과측정체계를 확인하고, 추가 투자 이전에 최소 실행기준과 검증자료를 확보하는 것을 권장합니다.'))
  new('09 | 전략별 선정근거 및 실행조건')
  for t in tops[:5]:
   sub(f'{t["code"]} · {t["name"]}')
   s.append(p(f'추천점수 {t["score"]:.2f}점. 산정요소: '+', '.join(f'{k} {v:.1f}' for k,v in t['factors'].items())+'.'))
   s.append(p('주요 실행과제: '+' / '.join(ACTIONS[t['code']])))
  new('10 | 보류전략 및 투자위험 검토')
  if deferred:
   for t in deferred:
    sub(f'{t["code"]} · {t["name"]}')
    s.append(p('보류 사유: '+' / '.join(t['reasons'] or ['선행조건 검토 필요'])))
  else:s.append(p('규칙기반 엔진에서 자동 보류된 전략은 없습니다. 그러나 투자여력과 사업위험은 별도 실사로 확인해야 합니다.'))
  new('11 | 90일 우선 실행계획')
  s.append(tbl([['기간','실행내용','검증자료']]+[[f'{i*30+1}~{(i+1)*30}일',' / '.join(ACTIONS[t['code']]),'실행담당자·완료증빙·KPI 기초값'] for i,t in enumerate(tops[:3])],widths=[29*mm,90*mm,51*mm]))
  note('90일 계획은 일정 예시이며 실제 기업의 인력·예산·의사결정체계를 확인한 뒤 조정합니다.')
  new('12 | 1~3년 성장전략 로드맵')
  s.append(tbl([['시기','전략목표','필수 검증조건'],['1차년도','핵심 병목 해소 및 경영기반 정비','재무·고객·운영 지표의 기준값 확정'],['2차년도','검증된 시장·제품 전략의 선택적 확장','수익성·고객유지·공급역량 검증'],['3차년도','조직·자금 여건을 고려한 성장고도화','투자성과·조직생산성·사업지속성 평가']],widths=[28*mm,75*mm,67*mm]))
  new('13 | 기업별 성과관리 및 재진단 설계')
  s.append(tbl([['주기','관리내용'],['월별','매출·현금흐름·핵심 KPI 실적 점검'],['3개월','실행과제 완료율 및 선행조건 확인'],['6개월','8대 경영역량 부분 재진단'],['12개월','DNA 성향·성장단계·전략 적합성 재평가']],widths=[40*mm,130*mm]))
  new('14 | AI 분석의견 및 전문 컨설턴트 검토')
  if ai:
   sub('AI 기반 진단해석')
   for para in ai.split('\n'):
    if para.strip():s.append(p(para))
   note('AI 생성 문장은 해석 보조자료이며, 진단수치와 추천순위는 결정론적 진단엔진 결과를 기준으로 합니다.')
  else:
   s.append(p('AI 분석이 비활성화되어 검증 가능한 규칙기반 진단해석만 제공됩니다. OPENAI_API_KEY를 설정하고 AI 생성을 요청하면 기업별 심층 서술이 추가됩니다.'))
  sub('컨설턴트 검토항목')
  s.append(p('① 재무자료 및 현금흐름 확인 ② 고객·시장검증 증빙 확인 ③ 경영목표의 실현가능성 점검 ④ 추천전략의 예산·인력 적합성 검토'))
  new('15 | 종합 경영제언 및 분석한계')
  s.append(p(f'{name}의 최우선 경영과제는 {tops[0]["name"] if tops else "추가진단"}입니다. 진단결과와 경영계획의 정합성을 검토하고, 90일 실행과제의 담당자·예산·성과지표를 확정하는 것을 권장합니다.'))
 else:
  pass
 sub('진단결과 활용 시 유의사항')
 for lim in r['limitations']:note('• '+lim)
 note('모든 기업명·재무현황·진단응답은 입력자료에 기반합니다. 외부 기업 비교나 투자성과 예측은 수행하지 않았습니다.')
 doc.build(s,onFirstPage=foot,onLaterPages=foot)
 return {'result':r,'mode':mode,'ai_used':bool(ai),'output':out}
