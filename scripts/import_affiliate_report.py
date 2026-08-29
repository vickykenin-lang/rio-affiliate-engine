#!/usr/bin/env python3
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INBOX=ROOT/'data/affiliate_reports/latest.json'
OUT=ROOT/'data/affiliate_attribution_state.json'
ALLOWED={'amazon_associates_report','earnkaro_report','cuelinks_report','other_verified_affiliate_report'}

def load(path, default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def number_or_none(v):
    if v is None:return None
    if isinstance(v,bool):raise ValueError('boolean metric prohibited')
    if not isinstance(v,(int,float)):raise ValueError('metric must be number or null')
    if v < 0:raise ValueError('negative metric prohibited')
    return v

def main():
    if not INBOX.exists():
        print('No affiliate report present; attribution remains UNKNOWN.')
        return 0
    raw=INBOX.read_bytes();report=json.loads(raw.decode('utf-8'))
    source=str(report.get('source') or '')
    if source not in ALLOWED:raise SystemExit('Unsupported affiliate report source')
    observed=str(report.get('observed_at_utc') or '')
    if not observed:raise SystemExit('observed_at_utc required')
    clicks=number_or_none(report.get('clicks'));orders=number_or_none(report.get('orders'));commission=number_or_none(report.get('commission_inr'));settled=number_or_none(report.get('settled_revenue_inr'))
    ref=str(report.get('source_reference') or '').strip()
    if not ref:raise SystemExit('source_reference required')
    state={
      'schema_version':1,
      'status':'AFFILIATE_SOURCE_IMPORTED',
      'policy':'NO_PURCHASE_OR_REVENUE_WITHOUT_SOURCE_EVIDENCE',
      'clicks':clicks,
      'orders':orders,
      'commission_inr':commission,
      'settled_revenue_inr':settled,
      'source':source,
      'source_reference':ref,
      'source_observed_at_utc':observed,
      'last_import_at_utc':datetime.now(timezone.utc).isoformat(),
      'evidence_sha256':hashlib.sha256(raw).hexdigest(),
      'accepted_sources':sorted(ALLOWED),
      'decision_guard':'Null remains UNKNOWN. Revenue success requires this traceable report evidence; activity/content cannot substitute.'
    }
    OUT.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Affiliate attribution imported:',source,'orders=',orders,'settled=',settled)
    return 0

if __name__=='__main__':raise SystemExit(main())
