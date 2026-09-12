#!/usr/bin/env python3
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]; errors=[]
p=json.loads((R/'data/creative_policy.json').read_text()); l=json.loads((R/'data/creative_cost_ledger.json').read_text()); a=json.loads((R/'data/nova_canvas_access.json').read_text())
if p.get('paid_generation_default')!='DENY': errors.append('paid generation must default DENY')
if p.get('max_images_per_request')!=1: errors.append('only one image per paid request is allowed')
if l.get('actual_spend',0)+l.get('reserved',0)>l.get('approved_budget',0): errors.append('ledger exceeds approved budget')
if a.get('paid_generation_performed') is not False: errors.append('probe must never perform paid generation')
if a.get('model_id')!='amazon.nova-canvas-v1:0': errors.append('unexpected model id')
print('CREATIVE GOVERNANCE: '+('FAIL' if errors else 'PASS'))
if errors: print('\n'.join('ERROR: '+x for x in errors));sys.exit(1)
