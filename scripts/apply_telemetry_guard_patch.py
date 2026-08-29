#!/usr/bin/env python3
from pathlib import Path

p=Path('scripts/autonomous_business_cycle.py')
s=p.read_text(encoding='utf-8')
old="ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT/'data/rio_work_status.json'; SNAPSHOT=ROOT/'data/dashboard_snapshot.json'; STATUS=ROOT/'data/status.json'; CONTROL=ROOT/'data/control.json'; AUDIT=ROOT/'data/autonomy_audit.jsonl'; SOUL_STATUS=ROOT/'data/soul_runtime_status.json'; COMMERCIAL_POLICY=ROOT/'data/COMMERCIAL_VALIDATION_POLICY.json'"
new=old+"; TELEMETRY=ROOT/'data/telemetry_state.json'; ATTRIBUTION=ROOT/'data/affiliate_attribution_state.json'"
if old in s and 'TELEMETRY=' not in s:s=s.replace(old,new)
old2="control=jload(CONTROL,{'kill_switch':False});memory=jload(WORK,{});snap=jload(SNAPSHOT,{});health=jload(STATUS,{});commercial_policy=jload(COMMERCIAL_POLICY,{});directive=victor_directive()"
new2="control=jload(CONTROL,{'kill_switch':False});memory=jload(WORK,{});snap=jload(SNAPSHOT,{});health=jload(STATUS,{});commercial_policy=jload(COMMERCIAL_POLICY,{});telemetry=jload(TELEMETRY,{});attribution=jload(ATTRIBUTION,{});directive=victor_directive()"
if old2 in s:s=s.replace(old2,new2)
needle="'business_snapshot':{k:snap.get(k,0) for k in ['ready_offers','blocked_offers','content_items','revenue_inr','net_profit_inr','instagram_posted']}}"
replace="'business_snapshot':{k:snap.get(k,0) for k in ['ready_offers','blocked_offers','content_items','revenue_inr','net_profit_inr','instagram_posted']},'telemetry_state':telemetry,'affiliate_attribution_state':attribution}"
if needle in s:s=s.replace(needle,replace)
rules_needle="Never fabricate merchant, product, commission, availability, purchase, revenue, or live-check evidence."
guard=" Never infer elapsed time from task text: compare real timestamps. TELEMETRY HARD RULE: null/unknown impressions, clicks, orders, commission or conversions are UNKNOWN, never zero. A no-click, no-conversion, A/B-test, or rotate-because-no-results decision is forbidden unless telemetry_state identifies a named live collector, the relevant metric is numeric, and the required observation window has actually elapsed. If telemetry is unavailable, choose another executable revenue action or improve telemetry infrastructure; do not pretend measurement occurred. Affiliate purchase/revenue decisions must use affiliate_attribution_state and traceable report evidence."
if rules_needle in s and 'TELEMETRY HARD RULE' not in s:s=s.replace(rules_needle,rules_needle+guard)
p.write_text(s,encoding='utf-8')
print('telemetry guard patch applied')
