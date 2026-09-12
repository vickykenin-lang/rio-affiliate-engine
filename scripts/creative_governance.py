#!/usr/bin/env python3
"""Creative prompt/package validation and append-only cost accounting."""
from __future__ import annotations
import copy, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; POLICY=json.loads((ROOT/'data/creative_policy.json').read_text())

def validate_prompt(prompt:str)->list[str]:
    p=prompt.casefold(); errors=[]
    if not prompt.strip(): errors.append('PROMPT_EMPTY')
    if len(prompt)>1024: errors.append('PROMPT_TOO_LONG')
    for term in POLICY['forbidden_prompt_terms']:
        if term.casefold() in p: errors.append('FORBIDDEN_PROMPT_TERM:'+term)
    return errors

def validate_package(package:dict)->list[str]:
    errors=[]
    if package.get('source_policy') not in POLICY['allowed_source_policies']: errors.append('SOURCE_POLICY_NOT_ALLOWED')
    caption=str(package.get('caption_text',''))
    if not all(x.casefold() in caption.casefold() for x in POLICY['required_disclosures']): errors.append('DISCLOSURE_MISSING')
    if POLICY['price_claims_allowed'] is False and package.get('contains_price_claim'): errors.append('PRICE_CLAIM_FORBIDDEN')
    if not str(package.get('creative_sha256','')).isalnum() or len(str(package.get('creative_sha256','')))!=64: errors.append('CREATIVE_HASH_INVALID')
    return errors

def reserve_cost(ledger:dict,campaign_id:str,request_id:str,estimate:float,at:str|None=None)->dict:
    if estimate<=0: raise ValueError('estimate must be positive')
    result=copy.deepcopy(ledger)
    if any(e['request_id']==request_id for e in result['entries']): return result
    available=float(result['approved_budget'])-float(result['reserved'])-float(result['actual_spend'])
    if estimate>available: raise PermissionError('BLOCKED_BUDGET')
    result['reserved']=round(float(result['reserved'])+estimate,6)
    result['entries'].append({'campaign_id':campaign_id,'request_id':request_id,'kind':'RESERVATION','estimated_cost':estimate,'actual_cost':None,'at':at or datetime.now(timezone.utc).isoformat(timespec='seconds')})
    return result

def record_actual(ledger:dict,request_id:str,actual:float,at:str|None=None)->dict:
    if actual<0: raise ValueError('actual cost cannot be negative')
    result=copy.deepcopy(ledger); reservation=next((e for e in result['entries'] if e['request_id']==request_id and e['kind']=='RESERVATION'),None)
    if not reservation: raise ValueError('reservation not found')
    if any(e['request_id']==request_id and e['kind']=='ACTUAL' for e in result['entries']): return result
    result['reserved']=round(float(result['reserved'])-float(reservation['estimated_cost']),6); result['actual_spend']=round(float(result['actual_spend'])+actual,6)
    result['entries'].append({'campaign_id':reservation['campaign_id'],'request_id':request_id,'kind':'ACTUAL','estimated_cost':reservation['estimated_cost'],'actual_cost':actual,'at':at or datetime.now(timezone.utc).isoformat(timespec='seconds')})
    return result
