#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/status.json'
PROVIDERS=ROOT/'data/provider_health.json'
ATTR=ROOT/'data/affiliate_attribution_state.json'
OUT=ROOT/'data/runtime_health.json'

def load(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def main():
    s=load(STATUS,{})
    p=load(PROVIDERS,{})
    a=load(ATTR,{})
    validators=bool(s.get('all_validators_pass'))
    provider_state=p.get('overall_provider_health','UNVERIFIED')
    attr_state=a.get('status','UNKNOWN')
    if not validators:
        overall='BLOCKED'
    elif provider_state in {'BLOCKED'}:
        overall='BLOCKED'
    elif provider_state in {'DEGRADED','UNVERIFIED'} or attr_state in {'WAITING_EXTERNAL','AWAITING_AFFILIATE_SOURCE'}:
        overall='DEGRADED'
    else:
        overall='HEALTHY'
    out={
      'schema_version':1,
      'checked_at_utc':datetime.now(timezone.utc).isoformat(),
      'overall_runtime_health':overall,
      'validator_health':'PASS' if validators else 'FAIL',
      'provider_health':provider_state,
      'affiliate_attribution_status':attr_state,
      'truth_rule':'all_validators_pass describes validator coverage only and must not be interpreted as full runtime health.'
    }
    OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
    return 0 if overall=='HEALTHY' else 2

if __name__=='__main__':raise SystemExit(main())
