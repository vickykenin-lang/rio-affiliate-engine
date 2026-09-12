#!/usr/bin/env python3
"""Build the public, read-only GitHub Pages campaign projection."""
import csv, json, os
from datetime import date
from pathlib import Path
from campaign_state import approval_is_valid

ROOT=Path(__file__).resolve().parents[1]; CAMPAIGNS=ROOT/'data/campaigns'; OUT=ROOT/'site/content/campaign-dashboard.json'
MACHINE=json.loads((ROOT/'data/campaign_state_machine.json').read_text(encoding='utf-8'))
FRESH_DAYS=int(os.environ.get('RIO_OFFER_FRESHNESS_DAYS','1'))

def main():
    records=[]; existing=set()
    for path in sorted(CAMPAIGNS.glob('*.json')):
        c=json.loads(path.read_text(encoding='utf-8')); i=c['identity']; existing.add(i['asin'])
        records.append({'campaign_id':c['campaign_id'],'state':c['state'],'revision':c['revision'],'candidate_id':i['candidate_id'],
          'title':i['product_title'],'asin':i['asin'],'score':i.get('candidate_score'),'availability':i.get('availability'),
          'offer_verified_at':i.get('offer_verified_at'),'legacy':c['governance'].get('legacy_import',False),
          'creative_approved':approval_is_valid(c,'creative'),'publish_approved':bool(c.get('creative')) and approval_is_valid(c,'publish'),
          'allowed_actions':sorted(MACHINE['transitions'].get(c['state'],{})),'history':c.get('history',[])})
    candidates=[]; today=date.today()
    with (ROOT/'data/product_candidates.csv').open(encoding='utf-8',newline='') as handle:
        for row in csv.DictReader(handle):
            if row['status']!='READY': continue
            age=(today-date.fromisoformat(row['observed_at'])).days; blockers=[]
            if age>FRESH_DAYS: blockers.append('FRESH_OFFER_VERIFICATION_REQUIRED')
            if row['merchant_product_id'] in existing: blockers.append('CAMPAIGN_ALREADY_EXISTS')
            candidates.append({'candidate_id':row['candidate_id'],'title':row['product_title'],'asin':row['merchant_product_id'],
              'score':float(row['commercial_score']),'verification_age_days':age,'eligible':not blockers,'blockers':blockers})
    candidates.sort(key=lambda x:(-x['score'],x['candidate_id'])); records.sort(key=lambda x:(x['legacy'],-(x['score'] or 0),x['campaign_id']))
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({'schema_version':1,'selection_limit':3,'candidates':candidates,'campaigns':records},indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
    print(f'campaign dashboard: {len(candidates)} candidates, {len(records)} campaigns -> {OUT}')
if __name__=='__main__': main()
