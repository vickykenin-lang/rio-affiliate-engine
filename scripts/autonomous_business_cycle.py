#!/usr/bin/env python3
"""Run one safe objective-driven RIO business cycle from persistent work memory."""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from telegram_chat import call_llm
from rio_autonomous_executor import execute as execute_plan
from rio_work_dashboard import record

ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT/'data/rio_work_status.json'; SNAPSHOT=ROOT/'data/dashboard_snapshot.json'; STATUS=ROOT/'data/status.json'; CONTROL=ROOT/'data/control.json'; AUDIT=ROOT/'data/autonomy_audit.jsonl'; SOUL_STATUS=ROOT/'data/soul_runtime_status.json'; COMMERCIAL_POLICY=ROOT/'data/COMMERCIAL_VALIDATION_POLICY.json'; TELEMETRY=ROOT/'data/telemetry_state.json'; ATTRIBUTION=ROOT/'data/affiliate_attribution_state.json'; EMERGENCY_PAUSE=ROOT/'data/emergency_pause_state.json'
IST=timezone(timedelta(hours=5,minutes=30)); BOT=(os.environ.get('TELEGRAM_BOT_TOKEN_RIO') or '').strip(); CHAT=(os.environ.get('TELEGRAM_CHAT_ID_RIO') or '').strip()
PILLARS={1:'website development/conversion/SEO',2:'new affiliate networks and product opportunities',3:'AdSense readiness and monetization',4:'product-led blog/content',5:'Flipkart or other commerce/platform expansion',6:'Instagram sales/content execution'}

def jload(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def paused(control):
    raw=control.get('maintenance_pause_until')
    if not raw:return False
    try:
        until=datetime.fromisoformat(raw)
        if until.tzinfo is None:until=until.replace(tzinfo=IST)
        return datetime.now(IST)<until.astimezone(IST)
    except Exception:return False

def soul_gate():
    soul=jload(SOUL_STATUS,{})
    checks=soul.get('checks') or {}
    required=(soul.get('valid') is True and checks.get('soul_present') is True and checks.get('objective_present') is True and checks.get('memory_present') is True and checks.get('lead_ai_declared') is True)
    return required,soul

def soul_failure_reason(soul):
    checks=soul.get('checks') or {}; failed=[k for k in ('soul_present','contract_markers','objective_present','memory_present','heartbeat_status_present','lead_ai_declared','validators_declared') if checks.get(k) is not True]
    return 'SOUL_HARD_GATE: autonomous execution is FAIL-CLOSED. Failed/missing checks: '+(', '.join(failed) if failed else 'runtime valid flag false')+'. Heartbeat, diagnostics, kill-switch and Founder interface remain alive.'

def tail_audit(n=6):
    try:return [json.loads(x) for x in AUDIT.read_text(encoding='utf-8').splitlines()[-n:] if x.strip()]
    except Exception:return []

def notify(text):
    if not BOT or not CHAT:return False
    data=urllib.parse.urlencode({'chat_id':CHAT,'text':text,'disable_web_page_preview':True}).encode();req=urllib.request.Request(f'https://api.telegram.org/bot{BOT}/sendMessage',data=data,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=20) as r:return bool(json.load(r).get('ok'))
    except Exception:return False

def completed(memory,limit=18):
    out=[]
    for x in reversed(memory.get('history') or []):
        if x.get('status')=='COMPLETED':
            t=' '.join(str(x.get('task') or '').lower().split())
            if t and t not in out:out.append(t)
            if len(out)>=limit:break
    return out

def pillar_for(text):
    t=(text or '').lower()
    if any(x in t for x in ['instagram','carousel','reel','social post']):return 6
    if any(x in t for x in ['flipkart','commerce platform','marketplace','merchant platform']):return 5
    if any(x in t for x in ['blog','guide','article','content']):return 4
    if any(x in t for x in ['adsense','ad monet','display ad']):return 3
    if any(x in t for x in ['affiliate network','affiliate program','new network','partner program']):return 2
    if any(x in t for x in ['website','site/','seo','index','comparison page','landing page','conversion']):return 1
    return None

def recent_pillars(memory,n=8):return [pillar_for(x.get('task')) for x in (memory.get('history') or []) if x.get('status')=='COMPLETED'][-n:]

def founder_only_blocker(text):
    t=str(text or '').upper()
    return any(k in t for k in ['CREDENTIAL','ACCOUNT IDENTITY','SECRET REQUIRED','BUDGET CEILING','IRREVERSIBLE','LEGAL JUDGMENT','SECURITY JUDGMENT','SYSTEM PAUSE','FOUNDER PAUSE'])

def victor_directive():
    try:
        payload=json.loads(os.environ.get('VICTOR_RIO_TASK_PAYLOAD','{}') or '{}')
        return str(payload.get('founder_message') or '').strip()[:5000]
    except Exception:return ''

def main():
    control=jload(CONTROL,{'kill_switch':False});memory=jload(WORK,{});snap=jload(SNAPSHOT,{});health=jload(STATUS,{});commercial_policy=jload(COMMERCIAL_POLICY,{});telemetry=jload(TELEMETRY,{});attribution=jload(ATTRIBUTION,{});emergency=jload(EMERGENCY_PAUSE,{});directive=victor_directive()
    if control.get('kill_switch') or health.get('all_validators_pass') is not True:return 0
    if emergency.get('global_pause_active') is True or emergency.get('department_pause_active') is True or str(emergency.get('system_state') or '').upper()=='PAUSED':
        record('PAUSED',current_task='Emergency pause active',engine='emergency-pause',validators='PAUSE_FAIL_CLOSED',result='Founder/Victor emergency pause blocks autonomous execution and external actions.',next_task=memory.get('next_task'),blocker='EMERGENCY_PAUSE_ACTIVE',founder_action_needed=False);return 0
    if paused(control):
        print('[autonomous_cycle] maintenance pause active until',control.get('maintenance_pause_until'));return 0
    soul_ok,soul=soul_gate()
    if not soul_ok:
        reason=soul_failure_reason(soul)
        record('BLOCKED',current_task='Soul hard execution gate',engine='soul-gate',validators='SOUL_HARD_FAIL',result=reason,next_task=memory.get('next_task'),blocker=reason,founder_action_needed=False)
        status=jload(STATUS,{});status['soul_runtime']={'mode':'hard_fail_closed','valid':False,'hard_fail_closed':True,'execution_effect':'AUTONOMOUS_EXECUTION_BLOCKED','failed_checks':[k for k,v in (soul.get('checks') or {}).items() if v is not True]};
        try:STATUS.write_text(json.dumps(status,indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
        except Exception:pass
        previous=(control.get('last_soul_hard_alert') or '')
        signature=json.dumps(soul.get('checks') or {},sort_keys=True)
        if previous!=signature:
            notify('🔴 RIO SOUL HARD GATE\n'+reason);control['last_soul_hard_alert']=signature
            try:CONTROL.write_text(json.dumps(control,indent=1,ensure_ascii=False)+'\n',encoding='utf-8')
            except Exception:pass
        print('[autonomous_cycle]',reason);return 0
    if memory.get('status')=='WORKING':return 0
    blocker_text=' '.join(str(memory.get(k) or '') for k in ('blocker','last_result','next_task'))
    if (memory.get('founder_action_needed') or memory.get('status') in {'BLOCKED','VICKY_ACTION_REQUIRED'}) and founder_only_blocker(blocker_text):return 0
    done=completed(memory);rp=recent_pillars(memory);counts={p:rp.count(p) for p in PILLARS};lastp=rp[-1] if rp else None;revenue_focus=float(snap.get('revenue_inr') or 0)<=0 and int(snap.get('ready_offers') or 0)>0;forced_rotate=(not revenue_focus) and len(rp)>=2 and rp[-1] is not None and rp[-1]==rp[-2];base_pillars=(1,4,6) if revenue_focus else tuple(PILLARS);eligible=[p for p in base_pillars if not(forced_rotate and p==lastp)];min_count=min(counts[p] for p in eligible);priority=list(eligible) if revenue_focus else [p for p in eligible if counts[p]==min_count]
    context={'soul_runtime':'VALID_HARD_GATE','commercial_validation_policy':commercial_policy,'victor_strategic_directive':directive,'status':memory.get('status','IDLE'),'last_completed':memory.get('last_completed'),'last_result':memory.get('last_result'),'next_task':memory.get('next_task'),'changed_files':memory.get('changed_files') or [],'recent_completed_task_keys':done,'recent_pillars':rp,'pillar_counts_recent':counts,'rotation_priority_pillars':priority,'zero_revenue_ready_offer_focus':revenue_focus,'eligible_pillars_this_cycle':list(base_pillars),'forced_rotate_away_from':lastp if forced_rotate else None,'recent_history':(memory.get('history') or [])[-14:],'recent_audit':tail_audit(),'business_snapshot':{k:snap.get(k,0) for k in ['ready_offers','blocked_offers','content_items','revenue_inr','net_profit_inr','instagram_posted']},'telemetry_state':telemetry,'affiliate_attribution_state':attribution}
    rules=("AUTONOMOUS REVENUE EXECUTION CYCLE. Soul hard gate has passed. Founder does NOT approve routine strategy, content, publishing preparation, execution, recovery, or next-action choices. Founder is required only for credentials/account identity, spend above configured ceiling, irreversible high-impact commitments, unresolved legal/security judgment, or explicit pause/objective change. Victor is the strategic navigation layer; use victor_strategic_directive as high-priority direction when present, while preserving RIO's autonomous execution judgment. PRIMARY AGENDA: generate verified real affiliate revenue as soon as practically possible. When verified revenue is zero and ready_offers > 0, IGNORE least-used-pillar balancing as a primary objective and choose the closest valid revenue/conversion action: conversion pages, high-intent content, internal linking, offer-page QA, distribution/publishing, traffic acquisition within authority, or another evidence-backed action with higher expected commercial impact. Planning/readiness documents and pillar rotation must not displace a directly executable commercial action unless they remove a verified blocker. Never fabricate merchant, product, commission, availability, purchase, revenue, or live-check evidence. Never infer elapsed time from task text: compare real timestamps. TELEMETRY HARD RULE: null/unknown impressions, clicks, orders, commission or conversions are UNKNOWN, never zero. A no-click, no-conversion, A/B-test, or rotate-because-no-results decision is forbidden unless telemetry_state identifies a named live collector, the relevant metric is numeric, and the required observation window has actually elapsed. If telemetry is unavailable, choose another executable revenue action or improve telemetry infrastructure; do not pretend measurement occurred. Affiliate purchase/revenue decisions must use affiliate_attribution_state and traceable report evidence. If no safe independent task exists, respond WAITING_EXTERNAL:. Return exactly one executable task and founder_message with PILLAR:<1-6>, task, why, changes, NEXT_TASK:. Memory:\n"+json.dumps(context,ensure_ascii=False))
    record('WORKING',current_task=memory.get('next_task') or 'Selecting highest-impact revenue task.',engine='selecting',validators='PRECHECK_PASS+SOUL_HARD_PASS',founder_action_needed=False);plan,engine=call_llm([],rules);summary=(plan.get('founder_message') or plan.get('summary') or '').strip()
    if plan.get('intent')!='execute':
        if summary.upper().startswith('WAITING_EXTERNAL:'):record('WAITING',current_task=memory.get('next_task') or 'Waiting for external evidence',engine=engine,validators='NOT_RUN',result=summary,next_task=memory.get('next_task'),blocker=None,founder_action_needed=False);return 0
        if founder_only_blocker(summary):
            record('VICKY_ACTION_REQUIRED',current_task=memory.get('next_task') or 'Founder-only boundary',engine=engine,validators='NOT_RUN',result=summary or 'Founder-only blocker.',blocker=summary,founder_action_needed=True);notify('⚠️ RIO FOUNDER ACTION REQUIRED\n'+summary[:3000]);return 0
        record('WAITING',current_task=memory.get('next_task') or 'Autonomous replanning',engine=engine,validators='NOT_RUN',result=summary or 'No executable task returned; replan next cycle.',next_task='Replan autonomously toward the closest valid revenue action.',blocker=None,founder_action_needed=False);return 0
    chosen=(plan.get('summary') or memory.get('next_task') or 'Autonomous revenue task').strip();ck=' '.join(chosen.lower().split());cp=pillar_for(summary+' '+chosen)
    if ck in done or (forced_rotate and cp==lastp):record('WAITING',current_task=chosen,engine=engine,validators='NOT_RUN',result='ANTI_REPEAT_GUARD: repeated task suppressed; next cycle must choose a different executable revenue action.',next_task='Choose a different highest-impact executable revenue action.',blocker=None,founder_action_needed=False);return 0
    record('WORKING',current_task=chosen,engine=engine,validators='RUNNING',founder_action_needed=False)
    result=execute_plan(plan,request_summary='AUTONOMOUS REVENUE: '+chosen,engine=engine)
    if not result.get('ok') and ('empty/null JSON artifact' in str(result.get('error')) or 'empty JSON artifact' in str(result.get('error')) or 'empty text artifact' in str(result.get('error'))):
        repair_rules=rules+"\nPREVIOUS PLAN FAILED STRICT PAYLOAD VALIDATION: "+str(result.get('error'))[:500]+". Retry the same safe task with corrected operation schema."
        retry_plan,retry_engine=call_llm([],repair_rules)
        if retry_plan.get('intent')=='execute':result=execute_plan(retry_plan,request_summary='AUTONOMOUS REVENUE RETRY: '+chosen,engine=retry_engine);engine=retry_engine
    changed=result.get('changed_paths') or []
    if result.get('ok'):
        nxt=None;low=summary.lower();marker='next_task:'
        if marker in low:nxt=summary[low.rfind(marker)+len(marker):].strip().splitlines()[0][:500] or None
        record('COMPLETED',current_task=chosen,engine=engine,changed_files=changed,validators='PASS',result=summary or 'Autonomous revenue task completed and validated.',next_task=nxt or 'Choose the next highest-impact action from evidence and revenue signals.',blocker=None,founder_action_needed=False);return 0
    status=result.get('status','FAILED');error=result.get('error','unknown');fn=founder_only_blocker(error);record('VICKY_ACTION_REQUIRED' if fn else status,current_task=chosen,engine=engine,changed_files=[],validators='FAIL',result=summary,next_task=memory.get('next_task'),blocker=error,founder_action_needed=fn)
    if fn:notify(f'⚠️ RIO FOUNDER ACTION REQUIRED\nTask: {chosen}\nBlocker: {error}'[:3500])
    return 0
if __name__=='__main__':sys.exit(main())