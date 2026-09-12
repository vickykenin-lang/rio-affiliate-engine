#!/usr/bin/env python3
"""Zero-generation-cost Nova Canvas access/model probe."""
import json, os
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data/nova_canvas_access.json'
MODEL='amazon.nova-canvas-v1:0'; REGION=os.environ.get('AWS_REGION','us-east-1')

def main():
    result={'schema_version':1,'provider':'amazon-bedrock','model_id':MODEL,'region':REGION,
            'checked_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'paid_generation_performed':False}
    try:
        import boto3
        client=boto3.client('bedrock',region_name=REGION)
        details=client.get_foundation_model(modelIdentifier=MODEL)['modelDetails']
        result.update(status='READY',model_name=details.get('modelName'),output_modalities=details.get('outputModalities',[]),
                      response_streaming_supported=details.get('responseStreamingSupported',False),error=None)
    except Exception as exc:
        name=type(exc).__name__; result.update(status='BLOCKED_ACCESS',error={'type':name,'message':str(exc)[:500]})
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n'); print(json.dumps(result))
    raise SystemExit(0 if result['status']=='READY' else 2)
if __name__=='__main__': main()
