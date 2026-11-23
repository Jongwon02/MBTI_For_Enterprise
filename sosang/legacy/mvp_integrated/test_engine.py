import json
from pathlib import Path
from engine import diagnose
from report import build_pdf
for name in ('sample_cafe','sample_service'):
 p=json.loads((Path(__file__).parent/(name+'.json')).read_text(encoding='utf-8'))
 r=diagnose(p)
 assert len(r['dna_code'])==4
 assert 0<=r['overall']<=100
 assert len(r['strategies'])==5
 for detailed in (False,True):
  data=build_pdf(r,detailed)
  assert data.startswith(b'%PDF') and len(data)>3000
  (Path(__file__).parent/(name+('_detailed' if detailed else '_basic')+'.pdf')).write_bytes(data)
 print(name,r['dna_code'],r['overall'],[(s['title'],s['priority']) for s in r['strategies'][:3]])
print('PASS')
