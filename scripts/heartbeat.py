#!/usr/bin/env python3
"""RIO heartbeat: self-monitoring runtime health loop with mandatory SOUL gate."""
import json, os, subprocess, sys, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

ROOT=os.path.join(os.path.dirname(__file__),"..")
IST=timezone(timedelta(hours=5,minutes=30))
REPO=os.environ.get("GITHUB_REPOSITORY","vickykenin-lang/rio-affiliate-engine")
TOK=os.environ.get("GITHUB_TOKEN","")
BOT=(os.environ.get("TELEGRAM_BOT_TOKEN_RIO") or "").strip()
CHAT=(os.environ.get("TELEGRAM_CHAT_ID_RIO") or "").strip()
OWNER="vickykenin-lang"
ALERT_STATE="data/heartbeat_alert_state.json"

def gh(path,data=None,method=None):
 req=urllib.request.Request(f"https://api.github.com/{path}",method=method,headers={"Authorization":f"Bearer {TOK}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
 body=json.dumps(data).encode() if data is not None else None
 with urllib.request.urlopen(req,body,timeout=30) as r:return json.load(r) if r.status!=204 else {}

def jload(p,d):
 try:
  with open(os.path.join(ROOT,p),encoding="utf-8") as f:return json.load(f)
 except Exception:return d

def jsave(p,o):
 path=os.path.join(ROOT,p);os.makedirs(os.path.dirname(path),exist_ok=True)
 with open(path,"w",encoding="utf-8") as f:json.dump(o,f,indent=1,ensure_ascii=False)

def notify(text):
 if not BOT or not CHAT:
  print("[heartbeat] Telegram secrets missing; alert not sent");return False
 data=urllib.parse.urlencode({'chat_id':CHAT,'text':text,'disable_web_page_preview':True}).encode()
 req=urllib.request.Request(f'https://api.telegram.org/bot{BOT}/sendMessage',data=data,method='POST')
 try:
  with urllib.request.urlopen(req,timeout=20) as r:body=json.load(r)
  return bool(body.get('ok'))
 except Exception as e:
  print('[heartbeat] Telegram alert failed:',e);return False

def run_script(name):
 try:
  r=subprocess.run([sys.executable,os.path.join(ROOT,'scripts',name)],cwd=ROOT,capture_output=True,text=True,timeout=120)
  out=(r.stdout or '')+(("\n"+r.stderr) if r.stderr else '')
  return r.returncode==0,out.strip()
 except Exception as e:return False,f'failed to run {name}: {e}'

control=jload('data/control.json',{'kill_switch':False,'kill_reason':None})
inbox=jload('data/inbox.json',{'messages':[]})
now=datetime.now(IST).isoformat(timespec='minutes')
try:issues=gh(f'repos/{REPO}/issues?state=open&per_page=50')
except Exception as e:print('[heartbeat] issue read failed:',e);issues=[]
for i in issues:
 labels=[l['name'] for l in i.get('labels',[])];title=(i.get('title') or '').upper();body=i.get('body') or ''
 try:
  if 'kill-switch' in labels or 'KILL SWITCH' in title:
   control['kill_switch']=True;control['kill_reason']=f"Issue #{i['number']} by {i['user']['login']} at {now}";gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
  elif title.startswith('RESUME') and i['user']['login']==OWNER:
   control['kill_switch']=False;control['kill_reason']=None;gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
  elif 'owner-message' in labels or 'MESSAGE TO RIO' in title:
   inbox['messages'].append({'at':now,'from':i['user']['login'],'issue':i['number'],'text':body[:2000]});gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
 except Exception as e:print('[heartbeat] issue handling failed:',e)
jsave('data/control.json',control);jsave('data/inbox.json',inbox)
if control.get('kill_switch'):
 status=jload('data/status.json',{});status.update({'updated':now,'kill_switch':True,'note_en':f"Paused by kill switch. {control.get('kill_reason','')}"});jsave('data/status.json',status);sys.exit(0)

production_ok,production_out=run_script('check_production.py')
dash_ok,dash_out=run_script('generate_dashboard.py')
validator_scripts={'production_live':None,'offer_integrity':'validate_offer_integrity.py','product_candidates':'validate_product_candidates.py','dashboard':'validate_dashboard.py','production_offer_gate':'validate_production_offer_gate.py'}
validators={}
for key,script in validator_scripts.items():
 ok,out=(production_ok,production_out) if script is None else run_script(script)
 validators[key]={'pass':ok,'detail':'\n'.join(out.splitlines()[-15:])};print(f"[heartbeat] {key}: {'PASS' if ok else 'FAIL'}")
validators_pass=all(v['pass'] for v in validators.values()) and dash_ok
snap=jload('data/dashboard_snapshot.json',{})
counts={k:snap.get(k,0) for k in ['product_candidates','ready_offers','blocked_offers','rejected_products','content_items','revenue_inr','cost_inr','net_profit_inr']};counts['production_verified']=bool(production_ok)
status=jload('data/status.json',{});status.update({'updated':now,'kill_switch':False,'dashboard_regenerated':dash_ok,'validators':validators,'all_validators_pass':validators_pass,'counts':counts,'heartbeat_interval_minutes':5,'runtime_primary_ai':'bedrock-qwen','runtime_fallbacks':['deepseek','bedrock-glm']})
jsave('data/status.json',status)

# Mandatory fail-closed SOUL preflight. soul_runtime reads the freshly persisted
# validator/AI binding above; autonomous execution is permitted only when it passes.
soul_ok,soul_out=run_script('soul_runtime.py')
soul_state=jload('data/soul_runtime_status.json',{})
soul_valid=bool(soul_ok and soul_state.get('valid') is True and soul_state.get('hard_fail_closed') is True)
all_pass=bool(validators_pass and soul_valid)
status=jload('data/status.json',{})
status['all_validators_pass']=all_pass
status['soul_runtime']={
 'mode':'hard_fail_closed',
 'valid':soul_valid,
 'hard_fail_closed':True,
 'soul_sha256':soul_state.get('soul_sha256'),
 'execution_effect':'ALLOWED' if soul_valid else 'AUTONOMOUS_EXECUTION_BLOCKED',
}
status['note_en']=(f"Heartbeat OK — {sum(1 for v in validators.values() if v['pass'])}/{len(validators)} validators passing; SOUL hard gate valid." if all_pass else '⚠ Heartbeat/SOUL failure — autonomous execution is fail-closed until recovery.')
jsave('data/status.json',status)
print(f"[heartbeat] soul_runtime: {'HARD_PASS' if soul_valid else 'HARD_FAIL'}")
if soul_out:print('[heartbeat] soul detail:','\n'.join(soul_out.splitlines()[-5:]))

prev=jload(ALERT_STATE,{'healthy':None,'soul_valid':None});was=prev.get('healthy');was_soul=prev.get('soul_valid')
if was is not None and was!=all_pass:
 if all_pass:notify('🟢 RIO RECOVERED\nHeartbeat, validators and SOUL hard gate are healthy again.')
 else:notify('🔴 RIO ISSUE DETECTED\nHeartbeat/validator/SOUL hard-gate failure. Autonomous execution is blocked until recovery.')
elif was_soul is True and not soul_valid:
 notify('🔴 RIO SOUL HARD GATE FAILED\nAutonomous execution is blocked until SOUL integrity recovers.')
jsave(ALERT_STATE,{'healthy':all_pass,'updated':now,'soul_valid':soul_valid})
print('heartbeat done',json.dumps({'ok':all_pass,'soul_valid':soul_valid,'counts':counts}))
if not all_pass:sys.exit(1)
