#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,default=None):
 try:return json.loads((ROOT/name).read_text(encoding='utf-8'))
 except Exception:return {} if default is None else default
status=load('data/status.json');provider=load('data/provider_health.json');runtime=load('data/runtime_health.json');telemetry=load('data/telemetry_state.json');attrib=load('data/affiliate_attribution_state.json');ig=load('data/instagram_run_status.json');snap=load('data/dashboard_snapshot.json')
attr_status=attrib.get('status','UNKNOWN')
blockers=[]
if attr_status=='AWAITING_AFFILIATE_SOURCE':blockers.append('AFFILIATE_REPORT_MISSING')
out={
 'schema_version':1,'generated_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),
 'technical_health':{'validators':'HEALTHY' if status.get('all_validators_pass') else 'BLOCKED','runtime':runtime.get('overall_status','UNKNOWN')},
 'provider_health':{'status':provider.get('overall_status','UNKNOWN'),'primary':status.get('runtime_primary_ai'),'fallbacks':status.get('runtime_fallbacks',[])},
 'publishing_health':{'status':'HEALTHY' if ig.get('status') in {'INSTAGRAM_POSTED','IDLE'} else ig.get('status','UNKNOWN'),'instagram_posted':ig.get('posted_count',snap.get('instagram_posted')),'pending':ig.get('pending_count')},
 'telemetry_health':{'status':telemetry.get('status','UNKNOWN'),'website':(telemetry.get('website') or {}).get('status','UNKNOWN'),'instagram':(telemetry.get('instagram') or {}).get('status','UNKNOWN'),'measured_clicks':(telemetry.get('website') or {}).get('clicks'),'sessions':(telemetry.get('website') or {}).get('sessions')},
 'attribution_health':{'status':'WAITING_EXTERNAL' if attr_status=='AWAITING_AFFILIATE_SOURCE' else attr_status,'source':attrib.get('source'),'clicks':attrib.get('clicks'),'orders':attrib.get('orders'),'approved_commission_inr':attrib.get('approved_commission_inr'),'settled_revenue_inr':attrib.get('settled_revenue_inr',0)},
 'revenue_evidence':{'verified':attr_status=='AFFILIATE_SOURCE_IMPORTED','settled_revenue_inr':attrib.get('settled_revenue_inr',0),'unknown_is_not_zero':True},
 'blockers':blockers,'counts':snap
}
for p in [ROOT/'data/dashboard_truth.json',ROOT/'site/dashboard/truth.json']:
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'status':'OK','blockers':blockers,'technical':out['technical_health'],'attribution':out['attribution_health']}))
