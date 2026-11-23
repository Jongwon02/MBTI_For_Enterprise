import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from pathlib import Path
st.set_page_config(page_title='Biz-DNA 소상공인 진단',layout='wide')
AREAS={'상권·입지':15,'상품·서비스':15,'고객관리':15,'마케팅·판로':10,'재무·수익':20,'점포운영':10,'디지털':5,'경영자·미래대응':10}
QUESTIONS={
'상권·입지':['주변 핵심 고객층의 특성을 파악하고 있다','상권 내 경쟁점포의 강약점을 정기적으로 확인한다','점포의 접근성·가시성 문제를 파악하고 있다','상권 수요 변화에 대응하고 있다'],
'상품·서비스':['주력상품의 차별화 요소가 명확하다','고객의 품질평가를 수집하고 개선한다','상품별 수익성을 파악하고 있다','가격이 고객가치와 원가를 반영한다'],
'고객관리':['단골고객 비중을 파악하고 있다','재방문을 유도하는 활동을 운영한다','고객 불만을 기록하고 개선한다','고객 이탈원인을 파악한다'],
'마케팅·판로':['온라인 점포정보를 최신으로 관리한다','홍보활동의 효과를 측정한다','신규고객 확보 채널을 운영한다','판매채널별 실적을 비교한다'],
'재무·수익':['월별 매출과 비용을 기록한다','고정비와 손익분기점을 파악한다','현금흐름과 지급일정을 관리한다','상품별 원가·마진을 관리한다'],
'점포운영':['재고·발주를 체계적으로 관리한다','서비스 품질 기준을 정하고 지킨다','업무별 소요시간을 관리한다','성수기와 비수기 인력운영 계획이 있다'],
'디지털':['POS 등 매출관리 도구를 활용한다','온라인 고객정보를 관리한다','반복업무의 자동화를 활용한다','데이터를 활용해 경영판단을 한다'],
'경영자·미래대응':['향후 1년 경영목표가 구체적이다','매출 감소 시 대응계획이 있다','필요한 교육·컨설팅을 활용한다','향후 업종·시장 변화에 대비한다']}
STRATEGIES={'재무·수익':('수익구조 개선','원가·고정비·상품별 마진을 점검하고 13주 현금흐름표를 작성'), '상권·입지':('상권 대응전략','시간대별 고객수요와 경쟁점포를 분석해 영업시간·상품구성 조정'), '상품·서비스':('주력상품 경쟁력 강화','고객평가 기반 주력상품 개선과 저수익 품목 정리'), '고객관리':('단골·재방문 확대','재방문율 측정, 고객불만 기록, 재방문 유도 프로그램'), '마케팅·판로':('신규고객 유입 강화','지도·리뷰·SNS 채널을 정비하고 홍보 성과 추적'), '점포운영':('운영효율 개선','재고·발주·업무 매뉴얼 표준화'), '디지털':('디지털 운영기반 구축','POS와 매출데이터를 연계하고 반복업무 자동화'), '경영자·미래대응':('경영계획 수립','분기별 목표·실행과제·성과지표 설정')}
font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if not Path(font).exists():
 import glob
 candidates=glob.glob('/usr/share/fonts/**/*NotoSansCJK*',recursive=True)
 font=candidates[0] if candidates else None
if font:
 try:pdfmetrics.registerFont(TTFont('Korean',font))
 except Exception:font=None

def analyze(scores,monthly_sales,monthly_cost,monthly_rent):
 overall=round(sum(scores[k]*w for k,w in AREAS.items())/100,1)
 profit=monthly_sales-monthly_cost
 risk=[]
 if profit<=0:risk.append('월간 영업현금수지 적자: 확장투자보다 유동성 개선 우선')
 if monthly_sales>0 and monthly_rent/monthly_sales>.2:risk.append('임대료/매출 비율 20% 초과: 고정비 부담 점검 필요')
 ranked=sorted(scores,key=lambda k:(scores[k],-AREAS[k]))
 if profit<=0:ranked=['재무·수익']+[k for k in ranked if k!='재무·수익']
 return overall,profit,risk,ranked[:3]

def pdf_report(name,sector,scores,overall,profit,risk,top,answers):
 buff=BytesIO(); doc=SimpleDocTemplate(buff,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=44,bottomMargin=44)
 f='Korean' if font else 'Helvetica';styles=getSampleStyleSheet()
 styles.add(ParagraphStyle(name='KoTitle',fontName=f,fontSize=19,leading=27,textColor=colors.HexColor('#11365A'),spaceAfter=18))
 styles.add(ParagraphStyle(name='KoHead',fontName=f,fontSize=12,leading=19,textColor=colors.HexColor('#117C89'),spaceBefore=15,spaceAfter=7))
 styles.add(ParagraphStyle(name='KoBody',fontName=f,fontSize=9.5,leading=16,spaceAfter=6))
 story=[Paragraph('Biz-DNA 소상공인 경영진단 보고서',styles['KoTitle']),Paragraph(f'기업명: {name}  |  업종: {sector}',styles['KoBody']),Paragraph(f'종합역량점수: {overall:.1f} / 100점',styles['KoHead'])]
 rows=[['진단영역','점수','기본가중치']]+[[k,f'{scores[k]:.1f}',f'{w}%'] for k,w in AREAS.items()]
 tab=Table(rows,colWidths=[240,90,90]);tab.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),f),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#123A60')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#EDF5F8')]),('BOTTOMPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8)]));story.append(tab)
 story.append(Paragraph('핵심 진단 및 경영위험',styles['KoHead']))
 story.append(Paragraph(f'월 매출과 입력 비용의 차이: {profit:,.0f}만원. 이 값은 세무상 영업이익이 아니며 비용 입력 범위에 따라 달라집니다.',styles['KoBody']))
 for r in risk:story.append(Paragraph('• '+r,styles['KoBody']))
 if not risk:story.append(Paragraph('입력값 기준 즉시 발동한 재무위험 규칙 없음. 추가 증빙 확인 필요.',styles['KoBody']))
 story.append(Paragraph('우선 경영개선 전략',styles['KoHead']))
 for i,k in enumerate(top,1):
  title,desc=STRATEGIES[k];story.append(Paragraph(f'{i}. {title} ({k} {scores[k]:.1f}점)',styles['KoBody']));story.append(Paragraph('실행과제: '+desc,styles['KoBody']))
 story.append(Paragraph('90일 실행계획',styles['KoHead']))
 story.append(Paragraph('1~30일: 핵심 문제의 기초자료 확보 및 현황 점검',styles['KoBody']))
 story.append(Paragraph('31~60일: 우선 전략 1~2개를 시범 적용하고 실적 기록',styles['KoBody']))
 story.append(Paragraph('61~90일: 매출·원가·재방문 등 성과 비교 후 개선안 확정',styles['KoBody']))
 story.append(Paragraph('주의: 자가응답 기반의 예비진단이며 외부 상권·재무자료로 검증되지 않았습니다. 점수·임계값은 실증 전 시범기준입니다.',styles['KoBody']))
 doc.build(story);return buff.getvalue()

st.title('Biz-DNA | 소상공인 경영진단')
st.caption('자가진단 MVP · 8대 역량 32문항 · 맞춤형 개선전략 · PDF 자동생성')
with st.form('diagnosis'):
 c1,c2=st.columns(2)
 with c1:
  name=st.text_input('점포명','우리동네카페');sector=st.selectbox('업종',['외식업','도소매업','생활서비스업','기타'])
  monthly_sales=st.number_input('월평균 매출액 (만원)',min_value=0.,value=2500.,step=100.)
 with c2:
  monthly_cost=st.number_input('월평균 비용 합계 (만원, 임대료 포함)',min_value=0.,value=2200.,step=100.)
  monthly_rent=st.number_input('월평균 임대료 (만원, 위 비용에 포함)',min_value=0.,value=250.,step=10.)
 st.caption('각 항목은 1점(전혀 아니다)~5점(매우 그렇다)으로 답변합니다. 비용에는 사업 운영 관련 지출을 일관되게 입력하세요.')
 answers={}
 for area,questions in QUESTIONS.items():
  with st.expander(area,expanded=False):
   for j,q in enumerate(questions):answers[f'{area}-{j}']=st.select_slider(q,options=[1,2,3,4,5],value=3,key=f'{area}-{j}')
 submitted=st.form_submit_button('진단 실행 및 보고서 생성',type='primary')
if submitted:
 if monthly_rent>monthly_cost:st.error('임대료가 비용 합계보다 큽니다. 입력값을 수정하세요.');st.stop()
 scores={area:round(sum(answers[f'{area}-{j}']-1 for j in range(4))/16*100,1) for area in AREAS}
 overall,profit,risk,top=analyze(scores,monthly_sales,monthly_cost,monthly_rent)
 st.subheader('종합진단 결과');st.metric('종합역량',f'{overall}점');st.bar_chart(pd.DataFrame({'영역':list(scores),'점수':list(scores.values())}).set_index('영역'))
 st.write('**우선 개선전략**')
 for i,k in enumerate(top,1):st.write(f'{i}. {STRATEGIES[k][0]} — {STRATEGIES[k][1]}')
 for r in risk:st.warning(r)
 data=pdf_report(name,sector,scores,overall,profit,risk,top,answers)
 st.download_button('PDF 경영진단 보고서 다운로드',data=data,file_name='BizDNA_small_business_report.pdf',mime='application/pdf')
