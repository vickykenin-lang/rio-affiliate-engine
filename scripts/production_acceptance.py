#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):
 try:return json.loads((ROOT/p).read_text(encoding='utf-8'))
 except Exception:return {}
prod=load('data/production_status.json');provider=load('data/provider_health.json');truth=load('data/dashboard_truth.json');audit=load('data/autonomous_executor_audit.json');e2e=load('data/e2e_regression_report.json');funnel=load('data/commercial_funnel_state.json');attrib=load('data/affiliate_attribution_state.json')
checks={'production_http_verified':bool(prod.get('verified')),'provider_healthy':provider.get('overall_provider_health')=='HEALTHY','executor_audit_pass':audit.get('status')=='PASS','e2e_technical_pass':e2e.get('technical_result')=='PASS','dashboard_truth_present':truth.get('schema_version')==1,'commercial_funnel_active':funnel.get('state')=='ACTIVE'}
technical='PASS' if all(checks.values()) else 'FAIL'
business='PASS' if funnel.get('first_verified_commission') is True else 'WAITING_EXTERNAL'
out={'schema_version':1,'accepted_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'technical_acceptance':technical,'business_outcome':business,'checks':checks,'external_blockers':([] if business=='PASS' else [attrib.get('blocker') or 'AFFILIATE_SOURCE_NOT_AVAILABLE']),'attribution_status':attrib.get('status'),'note':'Technical production acceptance is independent of merchant-side commission evidence.'}
(ROOT/'data/production_acceptance.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));raise SystemExit(0 if technical=='PASS' else 1)
