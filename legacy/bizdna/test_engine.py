import unittest, copy
from engine import diagnose, DiagnosticError
from create_examples import cases

class TestEngine(unittest.TestCase):
 def test_a(self):
  r=diagnose(cases['case_a'])
  self.assertEqual(r['dna']['type'],'GICO')
  self.assertEqual(r['stage']['code'],'S3')
  self.assertIn('ST06',[x['code'] for x in r['top_recommended']])
 def test_b(self):
  r=diagnose(cases['case_b'])
  self.assertEqual(r['dna']['type'],'GINO')
  self.assertEqual(r['stage']['code'],'S4')
  self.assertEqual(r['top_recommended'][0]['code'],'ST08')
 def test_missing_answer(self):
  p=copy.deepcopy(cases['case_a']); del p['answers']['dna']['D01']
  with self.assertRaises(DiagnosticError): diagnose(p)
 def test_bad_range(self):
  p=copy.deepcopy(cases['case_b']); p['answers']['competence']['A01']=7
  with self.assertRaises(DiagnosticError): diagnose(p)
 def test_market_gate(self):
  p=copy.deepcopy(cases['case_b']); p['answers']['stage']['customer']=2
  self.assertLessEqual(int(diagnose(p)['stage']['code'][1:]),2)
 def test_cash_gate(self):
  p=copy.deepcopy(cases['case_b']); p['flags']['cash_crisis']=True
  r=diagnose(p)
  self.assertEqual(next(x for x in r['strategies'] if x['code']=='ST11')['status'],'deferred')

if __name__=='__main__': unittest.main()
