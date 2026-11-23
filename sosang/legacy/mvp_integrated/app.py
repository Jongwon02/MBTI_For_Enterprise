import json
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import AREAS,QUESTIONS,DNA,diagnose
from report import build_pdf
st.set_page_config(page_title='Biz-DNA 소상공인 통합 경영진단',page_icon='📊',layout='wide')
st.markdown('''<style>.block-container{max-width:1220px;padding-top:2rem}h1,h2,h3{color:#123354}.stButton>button[kind="primary"]{background:#087e89;border:0}.metric-card{background:#eef6f7;padding:16px;border-radius:12px}</style>''',unsafe_allow_html=True)
st.title('Biz-DNA | 소상공인 통합 경영진단')
st.caption('점주 자가진단 · 16개 DNA 경영유형 · 8대 경영역량 · 위험신호 · 성장전략 · PDF 보고서')
with st.sidebar:
 st.header('진단 안내')
 st.write('① 점포정보 입력\n\n② 16개 DNA 성향문항\n\n③ 32개 경영역량문항\n\n④ 진단 실행 및 보고서 다운로드')
 st.warning('시범모형: 실제 상권데이터·카드매출·세무자료와 자동 연계되지 않습니다.')
 st.caption('점포정보는 이 앱에서 외부 서버로 전송하지 않으며 별도 DB 저장도 하지 않습니다. 배포 환경의 로그·보안 설정은 별도 점검 필요.')
example=st.selectbox('예시 데이터 불러오기',['직접 입력','동네카페 예시','생활서비스 예시'])
example_file={'동네카페 예시':'sample_cafe.json','생활서비스 예시':'sample_service.json'}.get(example)
loaded=json.loads((Path(__file__).parent/example_file).read_text(encoding='utf-8')) if example_file else None
with st.form('diagnosis'):
 st.subheader('01. 점포 및 경영현황')
 c1,c2,c3=st.columns(3)
 with c1:
  name=st.text_input('점포명',value=loaded['profile']['name'] if loaded else '')
  sector=st.selectbox('업종',['외식업','도소매업','생활서비스업','기타'],index=['외식업','도소매업','생활서비스업','기타'].index(loaded['profile']['sector']) if loaded else 0)
 with c2:
  sales=st.number_input('월평균 매출액 (만원)',min_value=0.,value=float(loaded['profile']['monthly_sales']) if loaded else 2000.,step=50.)
  cost=st.number_input('월평균 총비용 (만원, 임대료 포함)',min_value=0.,value=float(loaded['profile']['monthly_cost']) if loaded else 1700.,step=50.)
 with c3:
  rent=st.number_input('월평균 임대료 (만원, 총비용에 포함)',min_value=0.,value=float(loaded['profile']['monthly_rent']) if loaded else 200.,step=10.)
  target=st.selectbox('우선 경영목표',['수익성 개선','매출확대','단골확보','운영효율','사업전환'],index=0)
 st.subheader('02. 점포 DNA 경영성향 (16문항)')
 st.caption('왼쪽 성향 1점 ↔ 오른쪽 성향 5점. 두 방향에 우열은 없습니다.')
 dna={}
 for axis,items in DNA.items():
  with st.expander(axis+' · 4문항',expanded=False):
   dna[axis]=[]
   for i,(left,right) in enumerate(items):
    default=loaded['dna'][axis][i] if loaded else 3
    val=st.radio(f'{i+1}. {left} ↔ {right}',[1,2,3,4,5],index=default-1,horizontal=True,key=f'dna-{axis}-{i}')
    dna[axis].append(val)
 st.subheader('03. 8대 경영역량 (32문항)')
 st.caption('1점 전혀 아니다 / 3점 보통 / 5점 매우 그렇다. 실제 운영 여부를 기준으로 응답하세요.')
 answers={}
 for area,qs in QUESTIONS.items():
  with st.expander(f'{area} · 가중치 {AREAS[area]}%',expanded=False):
   answers[area]=[]
   for i,q in enumerate(qs):
    default=loaded['responses'][area][i] if loaded else 3
    val=st.radio(f'{i+1}. {q}',[1,2,3,4,5],index=default-1,horizontal=True,key=f'q-{area}-{i}')
    answers[area].append(val)
 submitted=st.form_submit_button('진단 실행 · 보고서 생성',type='primary',use_container_width=True)
if submitted:
 payload={'profile':{'name':name.strip() or '미입력 점포','sector':sector,'monthly_sales':sales,'monthly_cost':cost,'monthly_rent':rent,'target':target},'dna':dna,'responses':answers}
 try: result=diagnose(payload)
 except ValueError as e:st.error(str(e));st.stop()
 st.session_state['diagnosis']=(payload,result)
if 'diagnosis' in st.session_state:
 payload,r=st.session_state['diagnosis']
 st.divider();st.header('04. 자동 경영진단 결과')
 a,b,c,d=st.columns(4)
 a.metric('종합 경영역량',f"{r['overall']:.1f}점")
 b.metric('DNA 경영유형',r['dna_code'])
 c.metric('월 매출-비용 차액',f"{r['profit_proxy']:,.0f}만원")
 d.metric('임대료/매출',f"{r['rent_ratio']:.1f}%" if r['rent_ratio'] is not None else '산정 불가')
 if r['border_axes']:st.info('경계 성향 진단축: '+', '.join(r['border_axes'])+' (유형은 잠정 판정)')
 col1,col2=st.columns([1.6,1])
 with col1:
  st.subheader('8대 경영역량')
  df=pd.DataFrame({'영역':list(r['scores']),'점수':list(r['scores'].values())}).set_index('영역')
  st.bar_chart(df,height=340)
 with col2:
  st.subheader('DNA 성향지수')
  st.dataframe(pd.DataFrame([{'진단축':k,'A성향 점수':v} for k,v in r['dna_scores'].items()]),hide_index=True,use_container_width=True)
  st.write('**상대적 강점:** '+', '.join(r['strengths']))
  st.write('**우선 보완:** '+', '.join(r['weaknesses']))
 st.subheader('경영위험 신호')
 if r['risks']:
  for risk in r['risks']:st.warning(risk['text'])
 else:st.success('입력자료 기준 자동 위험규칙 미발동. 추가 증빙 확인 필요.')
 st.subheader('맞춤형 경영개선 전략')
 for i,x in enumerate(r['strategies'][:5],1):
  with st.expander(f"{i}순위 · {x['title']} (우선점수 {x['priority']:.1f})",expanded=i<=3):
   st.write('**실행과제:** '+x['action']);st.write('**성과지표:** '+x['kpi'])
 st.subheader('90일 실행 로드맵')
 st.dataframe(pd.DataFrame([{'기간':'1~30일','실행':'문제원인 검증 및 기초자료 정리'},{'기간':'31~60일','실행':'1~2순위 전략 시범실행 및 주간 점검'},{'기간':'61~90일','실행':'실행성과 분석·개선·재진단 계획'}]),hide_index=True,use_container_width=True)
 st.subheader('보고서 다운로드')
 p1,p2,p3=st.columns(3)
 p1.download_button('기본형 PDF 다운로드',build_pdf(r,False),file_name='BizDNA_기본형.pdf',mime='application/pdf',use_container_width=True)
 p2.download_button('정밀형 PDF 다운로드',build_pdf(r,True),file_name='BizDNA_정밀형.pdf',mime='application/pdf',use_container_width=True)
 p3.download_button('진단결과 JSON',json.dumps({'input':payload,'result':r},ensure_ascii=False,indent=2),file_name='BizDNA_result.json',mime='application/json',use_container_width=True)
 st.caption(r['evidence'])
