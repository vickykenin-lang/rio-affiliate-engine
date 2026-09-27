#!/usr/bin/env python3
"""Guarded launcher for RIO autonomous cycle.

Adds durable evidence semantics without weakening the existing executor:
- affiliate/report/attribution tasks cannot be reported as completed unless a
  traceable affiliate source has actually been imported;
- when external affiliate evidence is absent, the LLM is instructed to choose
  another executable revenue action instead of repeatedly selecting the same
  blocked collection/import task.
"""
import json, sys
from pathlib import Path
import autonomous_business_cycle as cycle

ROOT=Path(__file__).resolve().parents[1]
ATTR=ROOT/'data/affiliate_attribution_state.json'


def load_attr():
    try:return json.loads(ATTR.read_text(encoding='utf-8'))
    except Exception:return {}


def needs_affiliate_evidence(text):
    t=(text or '').lower()
    keys=('amazon associates report','affiliate report','affiliate attribution','attribution collection','verify traceable clicks','verify traceable commission','import and validate latest amazon')
    return any(k in t for k in keys)


_original_call_llm=cycle.call_llm
_original_execute=cycle.execute_plan


def guarded_call_llm(history, user_text):
    attr=load_attr()
    if attr.get('status')!='AFFILIATE_SOURCE_IMPORTED':
        user_text += (
            "\nDURABLE EXTERNAL BLOCKER: affiliate attribution evidence is not currently imported. "
            "Do NOT choose Amazon Associates report import/collection/attribution verification as the executable task until a real source report exists. "
            "Choose a different executable revenue/conversion action that does not require that missing external report."
        )
    return _original_call_llm(history,user_text)


def guarded_execute(plan, request_summary='', engine='unknown'):
    result=_original_execute(plan,request_summary=request_summary,engine=engine)
    combined=' '.join([request_summary or '', str(plan.get('summary') or ''), str(plan.get('founder_message') or '')])
    if result.get('ok') and needs_affiliate_evidence(combined):
        attr=load_attr()
        if attr.get('status')!='AFFILIATE_SOURCE_IMPORTED':
            return {
                'ok':False,
                'status':'WAITING_EXTERNAL',
                'error':'AFFILIATE_SOURCE_NOT_AVAILABLE: no traceable affiliate report has been imported; task cannot be marked completed.',
                'changed_paths':result.get('changed_paths') or []
            }
    return result


cycle.call_llm=guarded_call_llm
cycle.execute_plan=guarded_execute

if __name__=='__main__':
    raise SystemExit(cycle.main())
