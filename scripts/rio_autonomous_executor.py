#!/usr/bin/env python3
"""Guarded executor: policy, SOUL, semantic output validation and rollback."""
import json, os, py_compile, subprocess
from datetime import datetime, timezone, timedelta

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));IST=timezone(timedelta(hours=5,minutes=30))
AUDIT=os.path.join(ROOT,'data','autonomy_audit.jsonl');CONTROL=os.path.join(ROOT,'data','control.json')
PROTECTED={'.gitignore','data/RIO_3.0_DEFINITION.md','data/AUTONOMY_POLICY.md','data/TELEGRAM_CHAT_LOCKED.md','data/SOUL.md','data/soul_runtime_status.json','scripts/soul_runtime.py','scripts/heartbeat.py','scripts/rio_autonomous_executor.py','scripts/telegram_chat.py'}
ALLOWED_PREFIXES=('data/','site/','scripts/');ALLOWED_OPS={'write_text','write_json','append_text','maintenance_pause'}
VALIDATORS=['scripts/validate_offer_integrity.py','scripts/validate_product_candidates.py','scripts/validate_dashboard.py','scripts/validate_production_offer_gate.py']

def _rel(path):
 path=(path or '').replace('\\','/').lstrip('/');norm=os.path.normpath(path).replace('\\','/')
 if norm.startswith('../') or norm=='..' or os.path.isabs(path):raise ValueError('path escapes repository')
 return norm

def _allowed(path):
 p=_rel(path)
 if p in PROTECTED or p.startswith('.github/workflows/'):return False
 return p.startswith(ALLOWED_PREFIXES)

def _audit(record):
 os.makedirs(os.path.dirname(AUDIT),exist_ok=True)
 with open(AUDIT,'a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')

def _run(cmd):
 p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=120);out=((p.stdout or '')+(p.stderr or '')).strip();return p.returncode,out[-3000:]

def _jload(path,default):
 try:
  with open(path,encoding='utf-8') as f:return json.load(f)
 except Exception:return default

def _soul_preflight():
 state=_jload(os.path.join(ROOT,'data','soul_runtime_status.json'),{})
 ok=(state.get('valid') is True and state.get('hard_fail_closed') is True and state.get('mode')=='hard_fail_closed' and state.get('execution_effect')=='ALLOWED')
 return ok,state

def _validate_operation_payload(kind,op,path=None):
 if kind=='write_json':
  value=op.get('value')
  if value is None:raise ValueError(f'empty/null JSON artifact rejected: {path}')
  if isinstance(value,(dict,list)) and len(value)==0:raise ValueError(f'empty JSON artifact rejected: {path}')
 elif kind in {'write_text','append_text'}:
  content=op.get('content')
  if not isinstance(content,str) or not content.strip():raise ValueError(f'empty text artifact rejected: {path}')

def _validate_changed_artifacts(paths):
 for path in paths:
  if path=='data/control.json':continue
  full=os.path.join(ROOT,path)
  if not os.path.isfile(full) or os.path.getsize(full)==0:raise ValueError(f'artifact missing/empty after write: {path}')
  if path.endswith('.json'):
   value=_jload(full,None)
   if value is None or (isinstance(value,(dict,list)) and len(value)==0):raise ValueError(f'invalid/empty JSON artifact after write: {path}')
  else:
   with open(full,encoding='utf-8') as f:
    if not f.read().strip():raise ValueError(f'blank artifact after write: {path}')

def validate():
 results=[];scripts_dir=os.path.join(ROOT,'scripts')
 try:
  for name in os.listdir(scripts_dir):
   if name.endswith('.py'):py_compile.compile(os.path.join(scripts_dir,name),doraise=True)
  results.append({'test':'python_compile','ok':True,'output':'PASS'})
 except Exception as e:return False,[{'test':'python_compile','ok':False,'output':str(e)}]
 for script in VALIDATORS:
  code,out=_run(['python',script]);results.append({'test':script,'ok':code==0,'output':out})
  if code!=0:return False,results
 return True,results

def execute(plan,request_summary='',engine='deepseek'):
 ts=datetime.now(IST).isoformat(timespec='seconds');risk=str(plan.get('risk') or 'high').lower();ops=plan.get('operations') or []
 record={'timestamp':ts,'request':request_summary[:500],'engine':engine,'risk':risk,'operations':[],'result':None,'changed_paths':[],'validators':[]}
 soul_ok,_=_soul_preflight()
 if not soul_ok:record['result']='BLOCKED_SOUL_HARD_GATE';_audit(record);return {'ok':False,'status':'FAILED','error':'SOUL hard gate is not valid/ALLOWED'}
 if plan.get('intent')!='execute':record['result']='NO_EXECUTION';_audit(record);return {'ok':True,'status':'NO_EXECUTION','changed_paths':[],'validators':[]}
 if risk=='high':record['result']='BLOCKED_HIGH_RISK';_audit(record);return {'ok':False,'status':'VICKY_ACTION_REQUIRED','error':'high-risk change blocked'}
 if not isinstance(ops,list) or not ops:record['result']='BLOCKED_EMPTY_PLAN';_audit(record);return {'ok':False,'status':'FAILED','error':'empty execution plan'}
 if len(ops)>8:record['result']='BLOCKED_TOO_MANY_OPERATIONS';_audit(record);return {'ok':False,'status':'VICKY_ACTION_REQUIRED','error':'operation limit exceeded'}
 backups={}
 try:
  for op in ops:
   kind=op.get('op')
   if kind not in ALLOWED_OPS:raise ValueError(f'operation not allowed: {kind}')
   if kind=='maintenance_pause':
    minutes=int(op.get('minutes') or 0)
    if minutes<1 or minutes>240:raise ValueError('maintenance_pause minutes must be 1..240')
    if 'data/control.json' not in backups:backups['data/control.json']=(open(CONTROL,'rb').read() if os.path.exists(CONTROL) else None)
    control=_jload(CONTROL,{'kill_switch':False});until=datetime.now(IST)+timedelta(minutes=minutes);control['maintenance_pause_until']=until.isoformat(timespec='seconds');control['maintenance_pause_reason']=(op.get('reason') or 'Founder-requested system maintenance')[:300];control['maintenance_pause_set_at']=datetime.now(IST).isoformat(timespec='seconds')
    with open(CONTROL,'w',encoding='utf-8') as f:json.dump(control,f,indent=1,ensure_ascii=False);f.write('\n')
    record['operations'].append({'op':kind,'minutes':minutes});record['changed_paths'].append('data/control.json');continue
   path=_rel(op.get('path'))
   if not _allowed(path):raise PermissionError(f'protected/disallowed path: {path}')
   _validate_operation_payload(kind,op,path);full=os.path.join(ROOT,path);os.makedirs(os.path.dirname(full),exist_ok=True)
   if path not in backups:backups[path]=(open(full,'rb').read() if os.path.exists(full) else None)
   if kind=='write_json':
    with open(full,'w',encoding='utf-8') as f:json.dump(op.get('value'),f,indent=2,ensure_ascii=False);f.write('\n')
   else:
    with open(full,'a' if kind=='append_text' else 'w',encoding='utf-8') as f:f.write(op['content'])
   record['operations'].append({'op':kind,'path':path});record['changed_paths'].append(path)
  _validate_changed_artifacts(record['changed_paths'])
  ok,checks=validate();record['validators']=checks
  if not ok:raise RuntimeError('validation failed')
  record['result']='COMPLETED';_audit(record);return {'ok':True,'status':'COMPLETED','changed_paths':record['changed_paths'],'validators':checks}
 except Exception as e:
  for path,old in backups.items():
   full=os.path.join(ROOT,path)
   try:
    if old is None:
     if os.path.exists(full):os.remove(full)
    else:
     with open(full,'wb') as f:f.write(old)
   except Exception:pass
  record['result']='FAILED_ROLLED_BACK';record['error']=str(e)[:1000];_audit(record);return {'ok':False,'status':'FAILED_ROLLED_BACK','error':str(e),'validators':record['validators']}
