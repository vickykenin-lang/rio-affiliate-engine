#!/usr/bin/env python3
"""Deterministic regression for the final seven RIO technical closure items."""
import importlib.util, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load(path, default):
    try:return json.loads((ROOT/path).read_text(encoding='utf-8'))
    except Exception:return default

def require(cond,msg):
    if not cond: raise AssertionError(msg)

def import_file(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def main():
    # 1 affiliate ingestion truth
    attr=load('data/affiliate_attribution_state.json',{})
    require(attr.get('status') in {'WAITING_EXTERNAL','AWAITING_AFFILIATE_SOURCE','AFFILIATE_SOURCE_IMPORTED'},'invalid attribution state')
    if attr.get('status')!='AFFILIATE_SOURCE_IMPORTED':
        require(attr.get('orders') is None and attr.get('commission_inr') is None,'missing source must not fabricate orders/commission')

    # 2 runtime/external blocker separation
    p=subprocess.run([sys.executable,'scripts/runtime_health.py'],cwd=ROOT,capture_output=True,text=True)
    require(p.returncode==0,'runtime implementation should pass when only external affiliate evidence is missing')
    runtime=load('data/runtime_health.json',{})
    require(runtime.get('runtime_implementation_healthy') is True,'runtime implementation health missing')

    # 3 autonomous evidence integrity
    ex=import_file('rio_executor','scripts/rio_autonomous_executor.py')
    for protected in ('data/affiliate_attribution_state.json','data/provider_health.json','data/runtime_health.json','data/status.json','data/commercial_milestone_state.json','data/revenue_m0_live_probe.json'):
        require(ex._allowed(protected) is False,f'autonomous executor can mutate evidence artifact: {protected}')
    require(ex._allowed('data/content_review_report.json') is True,'safe governed data path unexpectedly blocked')

    # 4 dashboard truth model
    p=subprocess.run([sys.executable,'scripts/dashboard_truth_model.py'],cwd=ROOT,capture_output=True,text=True)
    require(p.returncode==0,'dashboard truth model failed')
    truth=load('data/dashboard_truth_model.json',{})
    require(truth.get('business_outcome_state') in {'UNKNOWN_EXTERNAL','VERIFIED_SOURCE'},'dashboard outcome truth missing')
    if truth.get('business_outcome_state')=='UNKNOWN_EXTERNAL':
        require(truth.get('orders') is None and truth.get('commission_inr') is None and truth.get('settled_revenue_inr') is None,'dashboard inferred business result without source')

    # 5 end-to-end truth regression includes telemetry -> commercial gate -> dashboard
    tel=load('data/telemetry_state.json',{})
    require(tel.get('status') in {'TELEMETRY_LIVE','PARTIAL_TELEMETRY','TELEMETRY_PARTIAL'},'telemetry not live/partial')
    p=subprocess.run([sys.executable,'scripts/commercial_milestone_gate.py'],cwd=ROOT,capture_output=True,text=True)
    require(p.returncode==0,'commercial milestone gate failed')
    milestone=load('data/commercial_milestone_state.json',{})
    require('revenue_claim_allowed' in milestone,'commercial evidence gate missing')

    # 6 fresh production acceptance prerequisites
    provider=load('data/provider_health.json',{})
    require(provider.get('overall_provider_health')=='HEALTHY','provider not healthy')
    status=load('data/status.json',{})
    require(status.get('all_validators_pass') is True,'canonical validators not passing')

    # 7 commercial funnel restart is evidence-gated
    probe=load('data/revenue_m0_live_probe.json',{})
    require(bool(probe),'live funnel probe missing')
    if milestone.get('revenue_claim_allowed') is not True:
        require(not (isinstance(attr.get('settled_revenue_inr'),(int,float)) and attr.get('settled_revenue_inr',0)>0 and attr.get('status')=='AFFILIATE_SOURCE_IMPORTED'),'positive settled evidence inconsistent with gate')

    print('FINAL_SEVEN_REGRESSION: PASS')
    return 0

if __name__=='__main__':raise SystemExit(main())
