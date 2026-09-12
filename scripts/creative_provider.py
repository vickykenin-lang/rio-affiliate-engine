#!/usr/bin/env python3
"""Replaceable creative provider contract with default-deny paid execution."""
from __future__ import annotations
import json, os, uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

ROOT=Path(__file__).resolve().parents[1]; ACCESS=ROOT/'data/nova_canvas_access.json'

class CreativeProvider(Protocol):
    def build_request(self,prompt:str,width:int,height:int,seed:int)->dict: ...
    def generate(self,request:dict,*,allow_paid:bool=False)->dict: ...

@dataclass
class NovaCanvasProvider:
    region:str='us-east-1'; model_id:str='amazon.nova-canvas-v1:0'
    def build_request(self,prompt:str,width:int=1080,height:int=1080,seed:int=0)->dict:
        if not prompt.strip() or len(prompt)>1024: raise ValueError('prompt must contain 1..1024 characters')
        if [width,height] not in json.loads((ROOT/'data/creative_policy.json').read_text())['allowed_dimensions']:
            raise ValueError('dimensions are not approved by creative policy')
        if not 0<=seed<=858993459: raise ValueError('seed outside Nova Canvas range')
        return {'taskType':'TEXT_IMAGE','textToImageParams':{'text':prompt},'imageGenerationConfig':{'numberOfImages':1,'width':width,'height':height,'quality':'standard','cfgScale':6.5,'seed':seed}}
    def generate(self,request:dict,*,allow_paid:bool=False)->dict:
        if not allow_paid: raise PermissionError('paid generation requires explicit allow_paid approval')
        access=json.loads(ACCESS.read_text(encoding='utf-8'))
        if access.get('status')!='READY': raise PermissionError('Nova Canvas access probe is not READY')
        if os.environ.get('RIO_PAID_GENERATION_APPROVED')!='YES': raise PermissionError('RIO_PAID_GENERATION_APPROVED is not YES')
        import boto3
        response=boto3.client('bedrock-runtime',region_name=self.region).invoke_model(modelId=self.model_id,body=json.dumps(request),contentType='application/json',accept='application/json')
        payload=json.loads(response['body'].read())
        return {'request_id':response.get('ResponseMetadata',{}).get('RequestId',str(uuid.uuid4())),'provider':'amazon-bedrock','model':self.model_id,'images':payload.get('images',[])}
