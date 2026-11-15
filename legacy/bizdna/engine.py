"""Biz-DNA 1.0: deterministic, explainable prototype diagnostic engine.
No third-party dependencies. All thresholds are provisional, not validated norms.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json

DOMAINS = {
 'A': ('경영전략·사업모델', .15), 'B': ('시장·고객·마케팅', .15),
 'C': ('제품·서비스·기술', .15), 'D': ('재무·자금관리', .15),
 'E': ('조직·창업팀', .10), 'F': ('생산·운영·품질', .10),
 'G': ('디지털·데이터', .05), 'H': ('성장잠재력·확장성', .15)
}
DNA_AXES = [('G','S','성장지향'),('I','E','혁신차별'),('N','C','시장개척'),('P','O','조직체계')]
STRATEGIES = {
 'ST01': ('사업모델 검증', {'A':.45,'B':.40,'H':.15}),
 'ST02': ('제품시장 적합성 확보', {'B':.50,'C':.35,'A':.15}),
 'ST03': ('시장·판로 확대', {'B':.55,'A':.15,'H':.30}),
 'ST04': ('브랜드·마케팅 고도화', {'B':.80,'G':.20}),
 'ST05': ('기술·제품 혁신', {'C':.80,'H':.20}),
 'ST06': ('수익구조 개선', {'D':.65,'F':.25,'A':.10}),
 'ST07': ('재무구조 및 자금관리', {'D':.90,'A':.10}),
 'ST08': ('조직·인재 역량 강화', {'E':.85,'A':.15}),
 'ST09': ('생산·운영체계 고도화', {'F':.80,'E':.20}),
 'ST10': ('디지털전환·AI 활용', {'G':.75,'F':.25}),
 'ST11': ('투자유치·스케일업', {'D':.35,'H':.35,'A':.30}),
 'ST12': ('신사업·사업전환', {'A':.40,'C':.30,'H':.30}),
}
GOAL_MATCH = {
 'profit': ['ST06','ST07','ST09'], 'market': ['ST03','ST04','ST02'],
 'product': ['ST05','ST02','ST12'], 'scale': ['ST08','ST09','ST11','ST03'],
 'funding': ['ST07','ST11'], 'stability': ['ST06','ST07','ST08']
}
STAGE_NAMES = {1:'사업모델 탐색기',2:'시장검증기',3:'사업화 안정기',4:'성장확장기',5:'규모화·재도약기'}
STAGE_WEIGHTS = {'product':.20,'customer':.20,'revenue':.20,'cash':.15,'operations':.15,'expansion':.10}

class DiagnosticError(ValueError): pass

def require_number(value: Any, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value,(int,float)) or not low <= value <= high:
        raise DiagnosticError(f'{label}: {low}~{high} 범위 숫자 필요')
    return float(value)

def diagnose(payload: dict[str,Any]) -> dict[str,Any]:
    company = payload.get('company',{})
    answers = payload.get('answers',{})
    dna = answers.get('dna',{})
    competence = answers.get('competence',{})
    stages = answers.get('stage',{})
    goals = payload.get('goals',[])
    flags = payload.get('flags',{})
    if not isinstance(goals,list) or any(g not in GOAL_MATCH for g in goals):
        raise DiagnosticError('goals: 허용된 목표 코드 리스트 필요')
    if not isinstance(flags,dict) or any(not isinstance(v,bool) for v in flags.values()):
        raise DiagnosticError('flags: 불리언 값 필요')
    axis_scores={}; axis_details={}; code=''
    for i,(a,b,name) in enumerate(DNA_AXES):
        values=[require_number(dna.get(f'D{n:02d}'),f'D{n:02d}',1,5) for n in range(i*6+1,i*6+7)]
        score=round(sum(x-1 for x in values)/24*100,2)
        axis_scores[name]=score
        chosen = a if score>=50 else b
        code+=chosen
        axis_details[name]={'score':score,'letter':chosen,'boundary':40<score<60}
    domain_scores={}; total=0
    for d,(name,weight) in DOMAINS.items():
        vals=[require_number(competence.get(f'{d}{n:02d}'),f'{d}{n:02d}',1,5) for n in range(1,9)]
        score=round(sum(x-1 for x in vals)/32*100,2)
        domain_scores[d]=score
        total+=score*weight
    total=round(total,2)
    stage_inputs={k:require_number(stages.get(k),f'stage.{k}',1,5) for k in STAGE_WEIGHTS}
    stage_index=sum(stage_inputs[k]*w for k,w in STAGE_WEIGHTS.items())
    provisional=min(5,max(1,int(stage_index+.5)))
    # Minimum evidence gates: cannot classify expansion without validated repeat customers and revenue.
    stage=provisional
    if stage>=4 and (stage_inputs['customer']<4 or stage_inputs['revenue']<4 or stage_inputs['operations']<3): stage=3
    if stage>=5 and (stage_inputs['operations']<4 or stage_inputs['expansion']<4): stage=4
    if stage>=3 and (stage_inputs['customer']<3 or stage_inputs['revenue']<2): stage=2
    if stage>=2 and stage_inputs['product']<2: stage=1
    risks=[]
    if flags.get('cash_crisis'): risks.append('현금흐름 위험')
    if flags.get('market_unvalidated'): risks.append('시장검증 미완료')
    if flags.get('negative_unit_margin'): risks.append('단위경제성 악화')
    if flags.get('founder_bottleneck'): risks.append('창업자 의존')
    if flags.get('capacity_shortage'): risks.append('공급능력 부족')
    if flags.get('funding_gap'): risks.append('성장자금 부족')
    if flags.get('service_overload'): risks.append('서비스 운영부담')
    priorities=[]
    for key,(title,weights) in STRATEGIES.items():
        urgency=sum((100-domain_scores[d])*w for d,w in weights.items())
        matching=sum(1 for g in goals if key in GOAL_MATCH[g])
        fit=min(100,40+25*matching + (10 if key=='ST08' and flags.get('founder_bottleneck') else 0))
        impact=min(100,45+20*matching + (10 if key=='ST06' and flags.get('negative_unit_margin') else 0))
        feasibility=75
        notes=[]; blocked=False
        if flags.get('cash_crisis') and key in ('ST03','ST05','ST11','ST12'):
            blocked=True; notes.append('현금위험 해소 전 대규모 확장·투자 보류')
        if flags.get('market_unvalidated') and key in ('ST03','ST04','ST11'):
            blocked=True; notes.append('유료고객 검증 선행')
        if flags.get('capacity_shortage') and key=='ST03':
            blocked=True; notes.append('공급능력 확보 선행')
        if flags.get('negative_unit_margin') and key in ('ST03','ST11'):
            blocked=True; notes.append('단위경제성 개선 선행')
        if flags.get('founder_bottleneck') and key=='ST08':
            urgency=min(100,urgency+25); notes.append('창업자 업무집중 해소')
        if flags.get('service_overload') and key in ('ST09','ST10'):
            urgency=min(100,urgency+25); notes.append('고객지원 병목 개선')
        if flags.get('funding_gap') and key=='ST07':
            urgency=min(100,urgency+20); notes.append('성장자금 조달여건 점검')
        if flags.get('negative_unit_margin') and key=='ST06':
            urgency=min(100,urgency+25); notes.append('단위경제성 개선')
        if stage<=2 and key in ('ST11','ST03'):
            blocked=True; notes.append('시장검증 단계의 선행과제 필요')
        score=round(.30*fit+.30*urgency+.25*impact+.15*feasibility,2)
        priorities.append({'code':key,'name':title,'score':score,'status':'deferred' if blocked else 'recommended',
                           'factors':{'fit':round(fit,2),'urgency':round(urgency,2),'impact':round(impact,2),'feasibility':feasibility},
                           'reasons':notes})
    priorities.sort(key=lambda x:(x['status']=='deferred',-x['score'],x['code']))
    return {'model_version':'1.0-prototype','company':company,'dna':{'type':code,'axes':axis_details},
            'competence':{'domains':domain_scores,'total':total},
            'stage':{'code':f'S{stage}','name':STAGE_NAMES[stage], 'weighted_index':round(stage_index,3),'gate_adjusted':stage!=provisional},
            'risks':risks,'strategies':priorities,'top_recommended':[s for s in priorities if s['status']=='recommended'][:5],
            'limitations':['가중치·임계값은 시범용 가설','자기보고식 응답이며 외부 증빙 검증 없음','추천점수는 실제 성과예측값이 아님']}

if __name__=='__main__':
    import sys
    if len(sys.argv)!=2:
        print('사용법: python engine.py input.json'); sys.exit(2)
    with open(sys.argv[1],encoding='utf-8') as f: data=json.load(f)
    print(json.dumps(diagnose(data),ensure_ascii=False,indent=2))
