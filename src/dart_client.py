from __future__ import annotations
import json,os,time,requests
from pathlib import Path
from typing import Any
from config import DART_BASE
class DartAPIError(RuntimeError): pass
class DartClient:
    def __init__(self,api_key:str|None=None,timeout:int=40):
        self.api_key=api_key or os.getenv("DART_API_KEY")
        if not self.api_key: raise DartAPIError("DART_API_KEY is missing.")
        self.timeout=timeout; self.s=requests.Session(); self.s.headers["User-Agent"]="HN_SD.BIO-OpenDART-Agent/2.0"
    def get_json(self,endpoint:str,params:dict[str,Any])->dict[str,Any]:
        q={**params,"crtfc_key":self.api_key}; last=None
        for attempt in range(4):
            try:
                r=self.s.get(f"{DART_BASE}/{endpoint}.json",params=q,timeout=self.timeout); r.raise_for_status(); p=r.json()
                if str(p.get("status")) in {"000","013"}: return p
                raise DartAPIError(f"OpenDART {endpoint}: {p.get('status')} {p.get('message','')}")
            except (requests.RequestException,ValueError) as e:
                last=e; time.sleep(1.5**attempt)
        raise DartAPIError(f"OpenDART request failed: {endpoint}: {last}")
    def list_filings(self,corp_code,start_date,end_date,detail_code):
        out=[]; page=1
        while True:
            p=self.get_json("list",{"corp_code":corp_code,"bgn_de":start_date,"end_de":end_date,"pblntf_ty":"A","pblntf_detail_ty":detail_code,"last_reprt_at":"Y","page_no":page,"page_count":100})
            b=p.get("list",[]) or []; out.extend(b); total=int(p.get("total_page",1) or 1)
            if page>=total or not b: break
            page+=1; time.sleep(.15)
        return out
    def get_financials_with_fallback(self,corp_code,year,reprt_code):
        for fs in ("CFS","OFS"):
            p=self.get_json("fnlttSinglAcntAll",{"corp_code":corp_code,"bsns_year":str(year),"reprt_code":reprt_code,"fs_div":fs})
            if str(p.get("status"))=="000" and p.get("list"): p["_fs_div_used"]=fs; return p
        return {"status":"013","message":"No financial statement data.","list":[]}
    @staticmethod
    def save_json(path:Path,payload:Any):
        path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
