#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/'data/status.json'
PROVIDERS=ROOT/'data/provider_health.json'
ATTR=ROOT/'data/affiliate_attribution_state.json'
OUT=ROOT/'data/runtime_health.json'

EXTERNAL_ATTR_STATES={'WAITING_EXTERNAL','AWAITING_AFFILIATE_SOURCE'}

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
    external_blocker = attr_state in EXTERNAL_ATTR_STATES

    if not validators or provider_state == 'BLOCKED':
        overall='BLOCKED'
    elif provider_state in {'DEGRADED','UNVERIFIED'}:
        overall='DEGRADED'
    elif external_blocker:
        overall='HEALTHY_EXTERNAL_BLOCKER'
    else:
        overall='HEALTHY'

    out={
      'schema_version':2,
      'checked_at_utc':datetime.now(timezone.utc).isoformat(),
      'overall_runtime_health':overall,
      'runtime_implementation_healthy': overall in {'HEALTHY','HEALTHY_EXTERNAL_BLOCKER'},
      'external_business_evidence_blocked': external_blocker,
      'validator_health':'PASS' if validators else 'FAIL',
      'provider_health':provider_state,
      'affiliate_attribution_status':attr_state,
      'truth_rule':'Runtime implementation health is separate from external affiliate evidence. Missing affiliate reports never imply zero orders/commission and do not make a healthy AI/runtime implementation degraded.'
    }
    OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out))
    return 0 if overall in {'HEALTHY','HEALTHY_EXTERNAL_BLOCKER'} else 2

if __name__=='__main__':raise SystemExit(main())
