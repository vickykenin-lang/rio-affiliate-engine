#!/usr/bin/env python3
from pathlib import Path
p=Path('scripts/autonomous_business_cycle.py')
s=p.read_text(encoding='utf-8')
old="COMMERCIAL_POLICY=ROOT/'data/COMMERCIAL_VALIDATION_POLICY.json'; TELEMETRY=ROOT/'data/telemetry_state.json'; ATTRIBUTION=ROOT/'data/affiliate_attribution_state.json'"
new=old+"; EMERGENCY_PAUSE=ROOT/'data/emergency_pause_state.json'"
if old in s and 'EMERGENCY_PAUSE=' not in s:s=s.replace(old,new,1)
old2="control=jload(CONTROL,{'kill_switch':False});memory=jload(WORK,{});snap=jload(SNAPSHOT,{});health=jload(STATUS,{});commercial_policy=jload(COMMERCIAL_POLICY,{});telemetry=jload(TELEMETRY,{});attribution=jload(ATTRIBUTION,{});directive=victor_directive()"
new2="control=jload(CONTROL,{'kill_switch':False});memory=jload(WORK,{});snap=jload(SNAPSHOT,{});health=jload(STATUS,{});commercial_policy=jload(COMMERCIAL_POLICY,{});telemetry=jload(TELEMETRY,{});attribution=jload(ATTRIBUTION,{});emergency=jload(EMERGENCY_PAUSE,{});directive=victor_directive()"
if old2 in s:s=s.replace(old2,new2,1)
needle="    if control.get('kill_switch') or health.get('all_validators_pass') is not True:return 0\n"
insert="    if control.get('kill_switch') or health.get('all_validators_pass') is not True:return 0\n    if emergency.get('global_pause_active') is True or emergency.get('department_pause_active') is True or str(emergency.get('system_state') or '').upper()=='PAUSED':\n        record('PAUSED',current_task='Emergency pause active',engine='emergency-pause',validators='PAUSE_FAIL_CLOSED',result='Founder/Victor emergency pause blocks autonomous execution and external actions.',next_task=memory.get('next_task'),blocker='EMERGENCY_PAUSE_ACTIVE',founder_action_needed=False);return 0\n"
if needle in s and 'PAUSE_FAIL_CLOSED' not in s:s=s.replace(needle,insert,1)
p.write_text(s,encoding='utf-8')
print('RIO emergency pause guard patched')
