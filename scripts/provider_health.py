#!/usr/bin/env python3
import json, os, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/provider_health.json'
BEDROCK_REGION=os.getenv('AWS_BEDROCK_REGION','us-east-1').strip() or 'us-east-1'
BEDROCK_URL=f'https://bedrock-mantle.{BEDROCK_REGION}.api.aws/v1/chat/completions'
BEDROCK_MODEL=os.getenv('RIO_BEDROCK_CONTENT_MODEL','qwen.qwen3-coder-next')


def _probe(url,key,model,provider,required):
    state={'provider':provider,'required':required,'credential_present':bool(key),'live_request_pass':False,'real_output_verified':False,'status':'BLOCKED' if required else 'OPTIONAL_UNAVAILABLE','error':None}
    if not key:
        state['error']='CREDENTIAL_MISSING'
        return state
    payload=json.dumps({'model':model,'messages':[{'role':'user','content':'Reply exactly: RIO_HEALTH_OK'}],'max_tokens':16,'temperature':0}).encode()
    req=urllib.request.Request(url,data=payload,headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            body=json.loads(r.read().decode())
        text=((body.get('choices') or [{}])[0].get('message') or {}).get('content','').strip()
        state['live_request_pass']=True
        state['real_output_verified']=bool(text)
        state['response_marker_match']='RIO_HEALTH_OK' in text
        state['status']='HEALTHY' if text else ('BLOCKED' if required else 'OPTIONAL_DEGRADED')
        if not text: state['error']='EMPTY_OUTPUT'
    except urllib.error.HTTPError as e:
        state['error']=f'HTTP_{e.code}'
        state['status']='BLOCKED' if required else 'OPTIONAL_UNAVAILABLE'
    except Exception as e:
        state['error']=type(e).__name__
        state['status']='BLOCKED' if required else 'OPTIONAL_UNAVAILABLE'
    return state


def bedrock_probe():
    return _probe(BEDROCK_URL,os.getenv('AWS_BEDROCK_API_KEY','').strip(),BEDROCK_MODEL,'bedrock-qwen',True)


def deepseek_probe():
    key=os.getenv('DEEPSEEK_API_KEY','').strip()
    enabled=os.getenv('RIO_ALLOW_DEEPSEEK_FALLBACK','0').strip().lower() in {'1','true','yes'}
    if not enabled:
        return {'provider':'deepseek','required':False,'enabled':False,'credential_present':bool(key),'live_request_pass':None,'real_output_verified':None,'status':'OPTIONAL_DISABLED','error':None}
    state=_probe('https://api.deepseek.com/chat/completions',key,'deepseek-chat','deepseek',False)
    state['enabled']=True
    return state


def main():
    providers=[bedrock_probe(),deepseek_probe()]
    required=[p for p in providers if p.get('required')]
    required_healthy=bool(required) and all(p.get('status')=='HEALTHY' and p.get('live_request_pass') is True and p.get('real_output_verified') is True for p in required)
    state={
      'schema_version':2,
      'checked_at_utc':datetime.now(timezone.utc).isoformat(),
      'primary_provider':'bedrock-qwen',
      'overall_provider_health':'HEALTHY' if required_healthy else 'BLOCKED',
      'providers':providers,
      'rule':'Only required providers determine overall provider health. Credential presence alone is not proof; live request and real output are required.'
    }
    OUT.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state))
    return 0 if required_healthy else 2

if __name__=='__main__': raise SystemExit(main())
