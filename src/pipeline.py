from __future__ import annotations
import csv,json,re
from datetime import datetime,timezone
from config import CORP_CODE,CORP_NAME,DART_FINANCIAL_START_YEAR,DART_VIEWER,FLOW_FIELDS,PEERS,PROCESSED_DIR,RAW_DIR,RAW_FINANCIAL_DIR,REPORT_NAMES,SITE_DATA_DIR,START_YEAR
from dart_client import DartClient
from financial_parser import calculate_ratios,normalize
def save(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
def classify(n):
    if "사업보고서" in n:return "annual"
    if "반기보고서" in n:return "half"
    if "분기보고서" in n:
        m=re.search(r"\((20\d{2})\.(03|09)\)",n)
        if m:return "quarter1" if m.group(2)=="03" else "quarter3"
    return None
def year_of(n,dt):
    m=re.search(r"\((20\d{2})\.(?:03|06|09|12)\)",n)
    if m:return int(m.group(1))
    m=re.search(r"사업연도\s*[:：]\s*(20\d{2})",n)
    if m:return int(m.group(1))
    try:return int(dt[:4])
    except:return None
def build_filings(client):
    start=START_YEAR; end=datetime.now(timezone.utc).year; rows=[]
    for detail in ("A001","A002","A003"):
        for raw in client.list_filings(CORP_CODE,f"{start}0101",f"{end}1231",detail):
            c=classify(raw.get("report_nm",""))
            if not c:continue
            r=dict(raw); r["business_year"]=year_of(r.get("report_nm",""),r.get("rcept_dt","")); r["report_category"]=c; r["report_category_name"]=REPORT_NAMES[c]; r["dart_url"]=DART_VIEWER+str(r.get("rcept_no","")); rows.append(r)
    rows=sorted({str(r.get("rcept_no")):r for r in rows if r.get("rcept_no")}.values(),key=lambda r:(r.get("business_year") or 0,r.get("rcept_dt","")))
    save(RAW_DIR/"filings.json",rows); save(SITE_DATA_DIR/"filings.json",rows); rd=RAW_DIR.parent/"reports"; rd.mkdir(parents=True,exist_ok=True)
    with (rd/"filings.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=["business_year","rcept_dt","report_nm","report_category","rcept_no","corp_name","flr_nm","rm","dart_url"]); w.writeheader()
        for r in rows:w.writerow({k:r.get(k,"") for k in w.fieldnames})
    return rows
def main():
    client=DartClient(); fs=build_filings(client); fmap={(r.get("business_year"),r.get("report_category")):r for r in fs}; end=datetime.now(timezone.utc).year
    annual=[]; half=[]; q1=[]; q3=[]; raw={}
    available={(r.get("business_year"),r.get("report_category")) for r in fs}
    for y in range(DART_FINANCIAL_START_YEAR,end+1):
        for cat,code,target,cum in (("annual","11011",annual,False),("half","11012",half,True),("quarter1","11013",q1,False),("quarter3","11014",q3,False)):
            path=RAW_FINANCIAL_DIR/f"{y}_{cat}.json"
            if (y,cat) not in available and not path.exists():
                continue
            payload=json.loads(path.read_text(encoding="utf-8")) if path.exists() and y<end else client.get_financials_with_fallback(CORP_CODE,y,code)
            DartClient.save_json(path,payload); raw[f"{y}_{cat}"]=payload
            if str(payload.get("status"))=="000" and payload.get("list"): target.append(normalize(payload,y,code,(fmap.get((y,cat)) or {}).get("rcept_dt"),cum))
    am={r["year"]:r for r in annual}; hm={r["year"]:r for r in half}; q1m={r["year"]:r for r in q1}; q3m={r["year"]:r for r in q3}; quarterly=[]
    for y in range(DART_FINANCIAL_START_YEAR,end+1):
        if y in q1m:q=dict(q1m[y]);q["period"]="Q1";quarterly.append(q)
        if y in hm and y in q1m:
            q=dict(hm[y]);q["period"]="Q2"
            for f in FLOW_FIELDS:q[f]=hm[y].get(f)-q1m[y].get(f) if hm[y].get(f) is not None and q1m[y].get(f) is not None else None
            quarterly.append(q)
        if y in q3m:q=dict(q3m[y]);q["period"]="Q3";quarterly.append(q)
        if y in am and y in q3m:
            q=dict(am[y]);q["period"]="Q4";cum=normalize(raw[f"{y}_quarter3"],y,"11014",q.get("period_end"),True)
            for f in FLOW_FIELDS:q[f]=am[y].get(f)-cum.get(f) if am[y].get(f) is not None and cum.get(f) is not None else None
            quarterly.append(q)
    for r in annual:r["period"]="Annual"
    for r in half:r["period"]="Half-year"
    annual=calculate_ratios(sorted(annual,key=lambda r:r["year"])); half=calculate_ratios(sorted(half,key=lambda r:r["year"]))
    order={"Q1":1,"Q2":2,"Q3":3,"Q4":4}; quarterly=calculate_ratios(sorted(quarterly,key=lambda r:(r["year"],order.get(r.get("period"),9))))
    out={"company":CORP_NAME,"ticker":"137310","corp_code":CORP_CODE,"updated_at_utc":datetime.now(timezone.utc).isoformat(),"annual":annual,"half":half,"quarterly":quarterly,"peers":PEERS,"coverage":{"requested_start_year":START_YEAR,"financial_api_start_year":DART_FINANCIAL_START_YEAR,"legacy_years":list(range(START_YEAR,DART_FINANCIAL_START_YEAR))},"notes":["OpenDART fnlttSinglAcntAll standard financial data is available from 2015 onward.","2010-2014 figures are left unavailable rather than fabricated.","EBITDA is calculated from operating income plus disclosed depreciation/amortization when available.","ROIC is an analytical estimate, not a company-reported KPI.","DPO/CCC use an estimated purchase proxy only when sufficient history exists."]}
    save(PROCESSED_DIR/"financials.json",out); save(SITE_DATA_DIR/"financials.json",out); save(PROCESSED_DIR/"run_status.json",{"updated_at_utc":out["updated_at_utc"],"filings":len(fs),"annual_rows":len(annual),"half_rows":len(half),"quarter_rows":len(quarterly)})
    print(json.dumps({"filings":len(fs),"annual":len(annual),"half":len(half),"quarterly":len(quarterly)},ensure_ascii=False))
if __name__=="__main__":main()
