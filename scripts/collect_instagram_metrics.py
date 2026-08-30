#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLISHED=ROOT/'data/ig_published.json'
OUT=ROOT/'data/telemetry_state.json'
TOKEN=(os.environ.get('IG_ACCESS_TOKEN_RIO') or '').strip()
VERSION=(os.environ.get('IG_GRAPH_VERSION') or 'v23.0').strip()
BASE=f'https://graph.facebook.com/{VERSION}'

def load(path, default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def get(path, params):
    q=urllib.parse.urlencode(params)
    req=urllib.request.Request(f'{BASE}/{path}?{q}',headers={'User-Agent':'RIO-Telemetry/1.1'})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
    except urllib.error.HTTPError as e:
        try: body=e.read().decode('utf-8',errors='replace')[:500]
        except Exception: body=''
        raise RuntimeError(f'HTTP_{e.code}: {body}') from None

def metric_value(payload, name):
    for item in payload.get('data') or []:
        if item.get('name')==name:
            vals=item.get('values') or []
            if vals:return vals[-1].get('value')
            if 'value' in item:return item.get('value')
    return None

def collect_metric(media_id, name):
    payload=get(f'{media_id}/insights',{'metric':name,'access_token':TOKEN})
    return metric_value(payload,name)

def main():
    state=load(OUT,{})
    state.update({'schema_version':1,'policy':'UNKNOWN_IS_NOT_ZERO'})
    state.setdefault('website',{'click_collector':'NOT_CONFIGURED','status':'METRICS_UNAVAILABLE','clicks':None,'sessions':None,'source':None})
    state.setdefault('decision_guard',{})
    state['decision_guard'].update({'allow_no_click_decision':False,'rule':'Only measured clicks from a named collector may support a no-click decision. Null/unknown is never zero.'})
    insta=state.setdefault('instagram',{})
    insta.update({'collector':'scripts/collect_instagram_metrics.py','graph_version':VERSION,'posts':insta.get('posts') or {}})
    now=datetime.now(timezone.utc).isoformat()
    if not TOKEN:
        insta.update({'status':'BLOCKED_MISSING_IG_ACCESS_TOKEN','last_attempt_at_utc':now})
        state['status']='AWAITING_TELEMETRY'
        OUT.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');return 0
    posted=(load(PUBLISHED,{}).get('posted') or {})
    successes=0
    for offer, meta in posted.items():
        media_id=str(meta.get('media_id') or '').strip()
        if not media_id:continue
        rec={'offer_id':offer,'media_id':media_id,'permalink':meta.get('permalink'),'product_name':meta.get('product_name'),'posted_at':meta.get('posted_at'),'clicks':None,'click_source':'UNAVAILABLE_FROM_INSTAGRAM_MEDIA_INSIGHTS'}
        try:
            # Keep the core media request deliberately small. Optional/deprecated fields must not blind the whole collector.
            fields=get(media_id,{'fields':'id,media_type,permalink,timestamp,like_count,comments_count','access_token':TOKEN})
            rec.update({k:fields.get(k) for k in ['media_type','permalink','timestamp','like_count','comments_count'] if k in fields})
            rec['collector_status']='MEDIA_OK'
            successes+=1

            metric_errors={}
            # Query metrics independently: one unsupported/deprecated metric must not invalidate all available telemetry.
            for metric in ('views','reach','saved','shares','total_interactions'):
                try:
                    value=collect_metric(media_id,metric)
                    key='saves' if metric=='saved' else metric
                    rec[key]=value
                except Exception as e:
                    key='saves' if metric=='saved' else metric
                    rec[key]=None
                    metric_errors[metric]=str(e)[:350]
            # Do not alias views to impressions. If impressions are not directly measured, keep them UNKNOWN.
            rec['impressions']=None
            rec['insights_status']='OK' if not metric_errors else ('PARTIAL' if any(rec.get(k) is not None for k in ('views','reach','saves','shares','total_interactions')) else 'UNAVAILABLE')
            if metric_errors:rec['metric_errors']=metric_errors
            rec['collected_at_utc']=now
        except Exception as e:
            rec.update({'collector_status':'FAILED','collector_error':str(e)[:500],'collected_at_utc':now})
        insta['posts'][offer]=rec
    insta['last_attempt_at_utc']=now
    if successes:
        insta.update({'status':'LIVE_OR_PARTIAL','last_success_at_utc':now})
        state['status']='PARTIAL_TELEMETRY_LIVE' if state['website'].get('status')!='LIVE' else 'TELEMETRY_LIVE'
    else:
        insta['status']='NO_POST_METRICS_COLLECTED';state['status']='AWAITING_TELEMETRY'
    OUT.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 0

if __name__=='__main__':raise SystemExit(main())
