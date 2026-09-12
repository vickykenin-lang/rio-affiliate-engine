#!/usr/bin/env python3
"""Governed paid creative worker. Never runs without approval and budget gates."""
from __future__ import annotations
import argparse,base64,hashlib,json,os,random,uuid
from pathlib import Path
from scripts.campaign_state import load_campaign,save_campaign,transition_campaign,utc_now
from scripts.creative_governance import release_reservation,reserve_cost,validate_package,validate_prompt
from scripts.creative_provider import NovaCanvasProvider
ROOT=Path(__file__).resolve().parents[1];LEDGER=ROOT/'data/creative_cost_ledger.json';CREATIVE_DIR=ROOT/'site/creatives'
def atomic_json(path,value):
 t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n');os.replace(t,path)
def run(campaign_id,expected_revision,prompt,caption,estimated_cost,request_id,seed=None):
 c=load_campaign(campaign_id)
 if c['revision']!=expected_revision:raise ValueError(f"stale revision: current={c['revision']}")
 if c['state'] not in {'APPROVED_FOR_CREATIVE','CREATIVE_CHANGES_REQUESTED'}:raise PermissionError('campaign is not approved for generation/correction')
 errors=validate_prompt(prompt)
 if errors:raise ValueError('prompt rejected: '+','.join(errors))
 ledger=reserve_cost(json.loads(LEDGER.read_text()),campaign_id,request_id,estimated_cost);atomic_json(LEDGER,ledger)
 attempt=sum(e['action'] in {'START_CREATIVE_GENERATION','START_CREATIVE_CORRECTION'} for e in c['history'])+1
 action='START_CREATIVE_CORRECTION' if c['state']=='CREATIVE_CHANGES_REQUESTED' else 'START_CREATIVE_GENERATION';payload={'attempt':attempt,'request_idempotency_key':request_id}
 if action=='START_CREATIVE_CORRECTION':payload['correction_attempt']=sum(e['action']=='START_CREATIVE_CORRECTION' for e in c['history'])+1
 c=transition_campaign(c,action,'rio-generation-worker','SYSTEM',c['revision'],payload);save_campaign(c)
 try:
  provider=NovaCanvasProvider();request=provider.build_request(prompt,1080,1350,seed if seed is not None else random.randint(0,858993459));result=provider.generate(request,allow_paid=True)
  if len(result['images'])!=1:raise RuntimeError('unexpected image count')
  image=base64.b64decode(result['images'][0],validate=True);sha=hashlib.sha256(image).hexdigest();version=(c.get('creative') or {}).get('version',0)+1
  CREATIVE_DIR.mkdir(parents=True,exist_ok=True);asset=CREATIVE_DIR/f'{campaign_id.lower()}-v{version}.png';asset.write_bytes(image)
  package={'version':version,'asset_path':asset.relative_to(ROOT).as_posix(),'creative_sha256':sha,'caption_version':version,'caption_text':caption,'caption_sha256':hashlib.sha256(caption.encode()).hexdigest(),'landing_page_sha256':hashlib.sha256(c['identity']['landing_page_url'].encode()).hexdigest(),'source_policy':'ORIGINAL_CONTEXTUAL','provider':result['provider'],'model':result['model'],'request_id':result['request_id'],'generated_at':utc_now(),'attempt':attempt,'estimated_cost':estimated_cost,'actual_cost':None,'contains_price_claim':False}
  errors=validate_package(package)
  if errors:raise ValueError('package rejected: '+','.join(errors))
  c=transition_campaign(c,'CREATIVE_GENERATION_SUCCEEDED','rio-generation-worker','SYSTEM',c['revision'],package);save_campaign(c);return c
 except Exception as exc:
  atomic_json(LEDGER,release_reservation(json.loads(LEDGER.read_text()),request_id,type(exc).__name__))
  c=transition_campaign(c,'CREATIVE_GENERATION_FAILED','rio-generation-worker','SYSTEM',c['revision'],{'error_type':type(exc).__name__,'request_idempotency_key':request_id});save_campaign(c);raise
def main():
 p=argparse.ArgumentParser();p.add_argument('campaign_id');p.add_argument('--expected-revision',type=int,required=True);p.add_argument('--prompt',required=True);p.add_argument('--caption',required=True);p.add_argument('--estimated-cost',type=float,required=True);p.add_argument('--request-id',default=str(uuid.uuid4()));a=p.parse_args();print(run(a.campaign_id,a.expected_revision,a.prompt,a.caption,a.estimated_cost,a.request_id)['state'])
if __name__=='__main__':main()
