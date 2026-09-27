#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):
 try:return json.loads((ROOT/p).read_text(encoding='utf-8'))
 except Exception:return {}
control=load('data/production_control.json');status=load('data/status.json');provider=load('data/provider_health.json');telemetry=load('data/telemetry_state.json');attrib=load('data/affiliate_attribution_state.json');ig=load('data/instagram_run_status.json');snap=load('data/dashboard_snapshot.json');work=load('data/rio_work_status.json')
checks={
 'production_active':control.get('production_state')=='ACTIVE',
 'validators_pass':status.get('all_validators_pass') is True,
 'heartbeat_15m':status.get('heartbeat_interval_minutes')==15,
 'primary_bedrock_qwen':status.get('runtime_primary_ai')=='bedrock-qwen',
 'deepseek_not_active_fallback':'deepseek' not in [str(x).lower() for x in status.get('runtime_fallbacks',[])],
 'provider_healthy':provider.get('overall_status')=='HEALTHY',
 'website_telemetry_live':(telemetry.get('website') or {}).get('status')=='LIVE',
 'instagram_telemetry_live':(telemetry.get('instagram') or {}).get('status') in {'LIVE_OR_PARTIAL','LIVE'},
 'instagram_not_blocked':ig.get('status') not in {'BLOCKED_OFFER','BLOCKED_CREDENTIALS','BLOCKED_VALIDATION'},
 'instagram_posted_13_plus':int(ig.get('posted_count') or snap.get('instagram_posted') or 0)>=13,
 'ready_offers_17_plus':int(snap.get('ready_offers') or 0)>=17,
 'attribution_truthful':attrib.get('status') in {'AFFILIATE_SOURCE_IMPORTED','AWAITING_AFFILIATE_SOURCE'},
 'missing_source_has_blocker':attrib.get('status')!='AWAITING_AFFILIATE_SOURCE' or attrib.get('blocker')=='AFFILIATE_REPORT_MISSING',
}
technical='PASS' if all(checks.values()) else 'FAIL'
commercial='PASS' if attrib.get('status')=='AFFILIATE_SOURCE_IMPORTED' else 'WAITING_EXTERNAL'
result={'schema_version':1,'checked_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'technical_result':technical,'commercial_result':commercial,'checks':checks,'external_blockers':([] if commercial=='PASS' else ['AFFILIATE_REPORT_MISSING']),'work_state':work.get('status')}
(ROOT/'data/e2e_regression_report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if technical=='PASS' else 1)
