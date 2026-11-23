import json
from pathlib import Path
from advanced import diagnose_v4,SECTOR_QUESTIONS
for f in ['sample_cafe.json','sample_service.json']:
 p=json.loads(Path(__file__).with_name(f).read_text(encoding='utf-8'))
 r=diagnose_v4(p)
 assert r['stage']['code']=='UNDETERMINED'
 assert 0<=r['overall']<=100
 assert len(r['strategies'])>=3
 p['sector_answers']={area:[5,4,4,3] for area in SECTOR_QUESTIONS[p['profile']['sector']]}
 p['observations']={'months_operating':30,'repeat_rate':50,'positive_cashflow_months':10,'channels':2,'staff':3,'sales_prev':p['profile']['monthly_sales']*.8}
 r2=diagnose_v4(p)
 assert r2['stage']['code']=='S4'
 assert len(r2['sector_diagnostics'])==3
 assert r2['confidence']['level']=='보통'
 print(f,r['overall'],r2['overall'],r2['stage']['code'])
from report import build_pdf
assert build_pdf(r2,True)[:4]==b'%PDF'
print('PASS')
