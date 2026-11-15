import json
from pathlib import Path
ROOT=Path(__file__).parent

def make(name,industry,dna,domains,stage,goals,flags):
    answers={'dna':{},'competence':{},'stage':stage}
    for i,score in enumerate(dna):
        # 6 answers per axis; round-robin distributes a desired average to legal integers.
        total=round(6+score/100*24)
        values=[1]*6
        for j in range(total-6): values[j%6]+=1
        for j,v in enumerate(values): answers['dna'][f'D{i*6+j+1:02d}']=v
    for d,score in domains.items():
        total=round(8+score/100*32)
        values=[1]*8
        for j in range(total-8): values[j%8]+=1
        for j,v in enumerate(values): answers['competence'][f'{d}{j+1:02d}']=v
    return {'company':{'name':name,'industry':industry},'answers':answers,'goals':goals,'flags':flags}

cases={
 'case_a':make('그린푸드랩','식품제조',[78,82,35,30],dict(zip('ABCDEFGH',[65,55,85,45,40,70,45,75])),
    {'product':4,'customer':3,'revenue':3,'cash':2,'operations':3,'expansion':3},
    ['profit','market','funding'],{'negative_unit_margin':True,'founder_bottleneck':True,'funding_gap':True}),
 'case_b':make('넥스트솔루션','B2B SaaS',[92,88,85,38],dict(zip('ABCDEFGH',[80,85,90,65,50,65,80,75])),
    {'product':5,'customer':4,'revenue':5,'cash':4,'operations':3,'expansion':4},
    ['scale','market'],{'founder_bottleneck':True,'service_overload':True})
}
for key,val in cases.items():
    (ROOT/f'{key}.json').write_text(json.dumps(val,ensure_ascii=False,indent=2),encoding='utf-8')
