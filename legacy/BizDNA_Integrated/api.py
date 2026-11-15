"""FastAPI integration. Launch: uvicorn api:app --host 0.0.0.0 --port 8000"""
import os, tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from engine import diagnose,DiagnosticError
from reports import generate
app=FastAPI(title='Biz-DNA 통합 진단·자동보고서',version='2.0.0')
class ReportRequest(BaseModel):
 payload:dict
 mode:str='basic'
 use_ai:bool=False
@app.get('/',response_class=HTMLResponse)
def home():
 return '''<!doctype html><html lang="ko"><meta charset="utf-8"><title>Biz-DNA 진단보고서</title><style>body{font-family:system-ui,sans-serif;background:#f3f7fa;color:#17344d;margin:0}main{max-width:950px;margin:45px auto;padding:30px;background:white;border-radius:18px;box-shadow:0 4px 30px #1233}h1{margin-top:0}textarea{width:100%;height:330px;box-sizing:border-box;font:13px monospace;padding:14px;border:1px solid #ccd8e0;border-radius:8px}button,select{padding:11px 16px;border-radius:8px;border:1px solid #cad8e0}button{background:#176d85;color:white;cursor:pointer}small{color:#5c6e7a}#status{white-space:pre-wrap;margin-top:18px}</style><main><h1>Biz-DNA 기업진단 자동보고서</h1><p>기업 진단 JSON을 입력하고 보고서 유형을 선택하세요.</p><textarea id="payload" placeholder="기업 진단 JSON을 붙여넣으세요"></textarea><p><select id="mode"><option value="basic">기본형 PDF</option><option value="advanced">정밀형 PDF</option></select> <label><input type="checkbox" id="ai"> AI 심층해석 (서버 API 키 설정 필요)</label> <button onclick="run()">PDF 보고서 생성</button></p><small>입력 데이터는 서버에서 처리됩니다. 민감한 기업자료를 사용하는 경우 인증·접근통제 및 별도 보안설정이 필요합니다.</small><div id="status"></div></main><script>async function run(){let status=document.querySelector('#status');try{let data=JSON.parse(document.querySelector('#payload').value);status.textContent='보고서 생성 중...';let r=await fetch('/report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payload:data,mode:document.querySelector('#mode').value,use_ai:document.querySelector('#ai').checked})});if(!r.ok)throw Error(await r.text());let blob=await r.blob();let a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='BizDNA_Report.pdf';a.click();status.textContent='PDF 생성 완료';setTimeout(()=>URL.revokeObjectURL(a.href),3000)}catch(e){status.textContent='오류: '+e.message}}</script></html>'''
@app.post('/diagnose')
def diagnostic(data:dict):
 try:return diagnose(data)
 except (DiagnosticError,ValueError,TypeError,KeyError) as e:raise HTTPException(status_code=422,detail=str(e))
@app.post('/report')
def report(req:ReportRequest):
 if req.mode not in ('basic','advanced'):raise HTTPException(status_code=422,detail='mode: basic 또는 advanced')
 try:
  result=diagnose(req.payload)
  fd,path=tempfile.mkstemp(prefix='bizdna_',suffix='.pdf');os.close(fd)
  generate(req.payload,path,req.mode,req.use_ai)
  return FileResponse(path,media_type='application/pdf',filename='BizDNA_Report.pdf',background=None)
 except (DiagnosticError,ValueError,TypeError,KeyError) as e:raise HTTPException(status_code=422,detail=str(e))
