#!/usr/bin/env python3
"""Overlay evidence-aware business truth onto dashboard_snapshot.json.
Keeps legacy numeric fields for compatibility while exposing whether they are measured,
unknown, or externally blocked. Never infers orders/commission/revenue from activity.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SNAP=ROOT/'data/dashboard_snapshot.json'
ATTR=ROOT/'data/affiliate_attribution_state.json'
TEL=ROOT/'data/telemetry_state.json'
RUNTIME=ROOT/'data/runtime_health.json'
MILESTONE=ROOT/'data/commercial_milestone_state.json'
OUT=ROOT/'data/dashboard_truth_model.json'

def load(path, default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def main():
    snap=load(SNAP,{})
    attr=load(ATTR,{})
    tel=load(TEL,{})
    runtime=load(RUNTIME,{})
    milestone=load(MILESTONE,{})
    imported=attr.get('status')=='AFFILIATE_SOURCE_IMPORTED'
    settled=attr.get('settled_revenue_inr') if imported else None
    commission=attr.get('commission_inr') if imported else None
    orders=attr.get('orders') if imported else None
    website=tel.get('website') or {}
    truth={
      'schema_version':1,
      'generated_at_utc':datetime.now(timezone.utc).isoformat(),
      'runtime_health':runtime.get('overall_runtime_health','UNKNOWN'),
      'telemetry_status':tel.get('status','UNKNOWN'),
      'website_clicks':website.get('clicks'),
      'website_clicks_state':'MEASURED' if isinstance(website.get('clicks'),int) else 'UNKNOWN',
      'affiliate_source_status':attr.get('status','UNKNOWN'),
      'orders':orders,
      'commission_inr':commission,
      'settled_revenue_inr':settled,
      'business_outcome_state':'VERIFIED_SOURCE' if imported else 'UNKNOWN_EXTERNAL',
      'commercial_milestone':milestone.get('status','UNKNOWN'),
      'revenue_claim_allowed':bool(milestone.get('revenue_claim_allowed')),
      'truth_rule':'Traffic/activity is not purchase or revenue evidence. Orders, commission and settled revenue remain UNKNOWN until an accepted affiliate source is imported.'
    }
    snap.update({
      'revenue_evidence_state':truth['business_outcome_state'],
      'affiliate_source_status':truth['affiliate_source_status'],
      'orders_verified':orders,
      'commission_inr_verified':commission,
      'settled_revenue_inr_verified':settled,
      'website_clicks':truth['website_clicks'],
      'telemetry_status':truth['telemetry_status'],
      'runtime_health':truth['runtime_health'],
      'commercial_milestone':truth['commercial_milestone'],
      'revenue_claim_allowed':truth['revenue_claim_allowed']
    })
    SNAP.write_text(json.dumps(snap,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    OUT.write_text(json.dumps(truth,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(truth))
    return 0

if __name__=='__main__':raise SystemExit(main())
