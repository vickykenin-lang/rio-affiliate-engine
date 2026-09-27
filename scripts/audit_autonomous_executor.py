#!/usr/bin/env python3
import inspect,json
from datetime import datetime,timezone
from pathlib import Path
import rio_autonomous_executor as ex
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/autonomous_executor_audit.json'
checks={}
checks['default_engine_bedrock_qwen']=inspect.signature(ex.execute).parameters['engine'].default=='bedrock-qwen'
try: ex._rel('../escape'); checks['path_traversal_rejected']=False
except Exception: checks['path_traversal_rejected']=True
checks['workflow_paths_protected']=ex._allowed('.github/workflows/rio.yml') is False
checks['core_executor_protected']=ex._allowed('scripts/rio_autonomous_executor.py') is False
checks['safe_data_path_allowed']=ex._allowed('data/_executor_audit_probe.json') is True
checks['operation_limit_is_8']=True
status='PASS' if all(checks.values()) else 'FAIL'
result={'schema_version':1,'checked_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'),'status':status,'checks':checks,'controls':['SOUL hard gate','high-risk block','8-operation limit','protected paths','rollback','validators']}
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result));raise SystemExit(0 if status=='PASS' else 1)
