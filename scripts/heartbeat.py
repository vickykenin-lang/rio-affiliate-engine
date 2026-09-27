#!/usr/bin/env python3
"""RIO heartbeat: self-monitoring runtime health loop with mandatory SOUL gate."""
import json, os, subprocess, sys, time, urllib.request, urllib.parse
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
now_utc=datetime.now(timezone.utc).isoformat(timespec='seconds')
try:issues=gh(f'repos/{REPO}/issues?state=open&per_page=50')
except Exception as e:print('[heartbeat] issue read failed:',e);issues=[]
for i in issues:
 labels=[l['name'] for l in i.get('labels',[])];title=(i.get('title') or '').upper();body=i.get('body') or ''
 actor=(i.get('user') or {}).get('login') or ''
 association=(i.get('author_association') or '').upper()
 trusted_actor=(actor==OWNER and association in {'OWNER','MEMBER','COLLABORATOR'})
 is_command=('kill-switch' in labels or 'KILL SWITCH' in title or title.startswith('RESUME') or 'owner-message' in labels or 'MESSAGE TO RIO' in title)
 if is_command and not trusted_actor:
  print(f"[heartbeat] ignored untrusted issue command #{i.get('number')} from {actor or 'unknown'}")
  continue
 try:
  if 'kill-switch' in labels or 'KILL SWITCH' in title:
   control['kill_switch']=True;control['kill_reason']=f"Issue #{i['number']} by {actor} at {now}";gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
  elif title.startswith('RESUME'):
   control['kill_switch']=False;control['kill_reason']=None;gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
  elif 'owner-message' in labels or 'MESSAGE TO RIO' in title:
   inbox['messages'].append({'at':now,'from':actor,'issue':i['number'],'text':body[:2000]});gh(f"repos/{REPO}/issues/{i['number']}",{'state':'closed'},'PATCH')
 except Exception as e:print('[heartbeat] issue handling failed:',e)
jsave('data/control.json',control);jsave('data/inbox.json',inbox)
if control.get('kill_switch'):
 status=jload('data/status.json',{});status.update({'updated':now,'last_heartbeat_utc':now_utc,'kill_switch':True,'note_en':f"Paused by kill switch. {control.get('kill_reason','')}"});jsave('data/status.json',status);sys.exit(0)

storefront_ok,storefront_out=run_script('generate_product_storefront.py')
public_ok,public_out=run_script('validate_public_content.py') if storefront_ok else (False,storefront_out)
production_ok,production_out=run_script('check_production.py')
if not production_ok:
 for attempt in range(1,4):
  print(f'[heartbeat] production check retry {attempt}/3 after transient failure')
  time.sleep(10)
  production_ok,production_out=run_script('check_production.py')
  if production_ok:break
dash_ok,dash_out=run_script('generate_dashboard.py')
validator_scripts={'storefront_generation':'__storefront__','public_content':'__public__','production_live':None,'offer_integrity':'validate_offer_integrity.py','product_candidates':'validate_product_candidates.py','campaigns':'validate_campaigns.py','creative_governance':'validate_creative_governance.py','dashboard':'validate_dashboard.py','production_offer_gate':'validate_production_offer_gate.py','commercial_plan':'validate_commercial_plan.py'}
validators={}
for key,script in validator_scripts.items():
 if script=='__storefront__':ok,out=storefront_ok,storefront_out
 elif script=='__public__':ok,out=public_ok,public_out
 else:ok,out=(production_ok,production_out) if script is None else run_script(script)
 validators[key]={'pass':ok,'detail':'\n'.join(out.splitlines()[-15:])};print(f"[heartbeat] {key}: {'PASS' if ok else 'FAIL'}")
validators_pass=all(v['pass'] for v in validators.values()) and dash_ok
snap=jload('data/dashboard_snapshot.json',{})
counts={k:snap.get(k,0) for k in ['product_candidates','ready_offers','blocked_offers','rejected_products','content_items','revenue_inr','cost_inr','net_profit_inr']};counts['production_verified']=bool(production_ok)
ig_state=jload('data/ig_published.json',{'posted':{}})
instagram_posted=len(ig_state.get('posted') or {})
status=jload('data/status.json',{});status.update({
 'updated':now,
 'last_heartbeat_utc':now_utc,
 'kill_switch':False,
 'dashboard_regenerated':dash_ok,
 'validators':validators,
 'all_validators_pass':validators_pass,
 'counts':counts,
 'heartbeat_interval_minutes':15,
 'runtime_primary_ai':'bedrock-qwen',
 'runtime_fallbacks':['bedrock-glm'],
 'ready_offers':counts.get('ready_offers',0),
 'content_items':counts.get('content_items',0),
 'revenue_inr':counts.get('revenue_inr',0),
 'net_profit_inr':counts.get('net_profit_inr',0),
 'instagram_posted':instagram_posted,
})
jsave('data/status.json',status)

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
print('heartbeat done',json.dumps({'ok':all_pass,'soul_valid':soul_valid,'counts':counts,'instagram_posted':instagram_posted,'heartbeat_interval_minutes':15}))
if not all_pass:sys.exit(1)
