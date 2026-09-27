#!/usr/bin/env python3
import json, os, urllib.parse, urllib.request, urllib.error

token=(os.environ.get('IG_ACCESS_TOKEN_RIO') or '').strip()
version=(os.environ.get('IG_GRAPH_VERSION') or 'v23.0').strip()
if not token:
    print(json.dumps({'instagram_auth':'MISSING'}))
    raise SystemExit(3)

host='graph.instagram.com' if token.upper().startswith('IGAA') else 'graph.facebook.com'
query=urllib.parse.urlencode({'fields':'id,username','access_token':token})
req=urllib.request.Request(f'https://{host}/{version}/me?{query}',headers={'User-Agent':'RIO-Instagram-Auth-Probe/1.0'})
try:
    with urllib.request.urlopen(req,timeout=25) as r:
        payload=json.load(r)
except urllib.error.HTTPError as e:
    body=e.read().decode('utf-8',errors='replace')[:500]
    print(json.dumps({'instagram_auth':'AUTH_FAILED','graph_host':host,'http_status':e.code,'error':body}))
    raise SystemExit(4)
except Exception as e:
    print(json.dumps({'instagram_auth':'PROBE_ERROR','graph_host':host,'error':str(e)[:500]}))
    raise SystemExit(5)

if not str(payload.get('id') or '').strip():
    print(json.dumps({'instagram_auth':'AUTH_FAILED','graph_host':host,'error':'NO_ACCOUNT_ID'}))
    raise SystemExit(4)
print(json.dumps({'instagram_auth':'TOKEN_VALID','graph_host':host,'account_id_present':True,'username_present':bool(payload.get('username'))}))
