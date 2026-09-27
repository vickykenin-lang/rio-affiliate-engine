#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/provider_health.json'

def deepseek_probe():
    key=os.getenv('DEEPSEEK_API_KEY','').strip()
    state={'provider':'deepseek','credential_present':bool(key),'live_request_pass':False,'real_output_verified':False,'status':'BLOCKED'}
    if not key:
        state['error']='CREDENTIAL_MISSING'; return state
    payload=json.dumps({'model':'deepseek-chat','messages':[{'role':'user','content':'Reply exactly: RIO_HEALTH_OK'}],'max_tokens':16,'temperature':0}).encode()
    req=urllib.request.Request('https://api.deepseek.com/chat/completions',data=payload,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=20) as r:
            body=json.loads(r.read().decode())
        text=((body.get('choices') or [{}])[0].get('message') or {}).get('content','').strip()
        state['live_request_pass']=True
        state['real_output_verified']=bool(text)
        state['status']='HEALTHY' if text else 'DEGRADED'
        state['response_marker_match']='RIO_HEALTH_OK' in text
    except urllib.error.HTTPError as e:
        state['error']=f'HTTP_{e.code}'
    except Exception as e:
        state['error']=type(e).__name__
    return state

def bedrock_probe():
    key=os.getenv('AWS_BEDROCK_API_KEY','').strip()
    return {'provider':'bedrock-qwen','credential_present':bool(key),'live_request_pass':None,'real_output_verified':None,'status':'UNVERIFIED_LIVE' if key else 'BLOCKED','error':None if key else 'CREDENTIAL_MISSING'}

def main():
    providers=[deepseek_probe(),bedrock_probe()]
    degraded=any(p['status'] in {'BLOCKED','DEGRADED'} for p in providers)
    state={'schema_version':1,'checked_at_utc':datetime.now(timezone.utc).isoformat(),'overall_provider_health':'DEGRADED' if degraded else 'HEALTHY','providers':providers,'rule':'Credential presence is not proof of live provider health or real output.'}
    OUT.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state))
    return 0 if not degraded else 2

if __name__=='__main__': raise SystemExit(main())
