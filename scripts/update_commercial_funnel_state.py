#!/usr/bin/env python3
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):
 try:return json.loads((ROOT/p).read_text(encoding='utf-8'))
 except Exception:return {}
snap=load('data/dashboard_snapshot.json');tele=load('data/telemetry_state.json');attrib=load('data/affiliate_attribution_state.json');ig=load('data/instagram_run_status.json')
commission=attrib.get('approved_commission_inr')
settled=attrib.get('settled_revenue_inr',0) or 0
verified=attrib.get('status')=='AFFILIATE_SOURCE_IMPORTED' and ((isinstance(commission,(int,float)) and commission>0) or settled>0)
out={'schema_version':1,'updated_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'state':'ACTIVE','goal':'FIRST_VERIFIED_COMMISSION','ready_offers':snap.get('ready_offers',0),'instagram_posted':ig.get('posted_count',snap.get('instagram_posted',0)),'website_telemetry':{'status':(tele.get('website') or {}).get('status','UNKNOWN'),'measured_clicks':(tele.get('website') or {}).get('clicks'),'sessions':(tele.get('website') or {}).get('sessions')},'attribution_status':attrib.get('status','UNKNOWN'),'external_blocker':attrib.get('blocker') if attrib.get('status')=='AWAITING_AFFILIATE_SOURCE' else None,'first_verified_commission':verified,'approved_commission_inr':commission if attrib.get('status')=='AFFILIATE_SOURCE_IMPORTED' else None,'settled_revenue_inr':settled,'next_executable_action':'Improve qualified traffic and conversion paths using measured website/Instagram telemetry while awaiting merchant attribution evidence.' if not verified else 'Scale evidence-backed traffic and conversion paths using verified commission data.','truth_rule':'UNKNOWN_IS_NOT_ZERO; commission is verified only from imported merchant evidence.'}
(ROOT/'data/commercial_funnel_state.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
