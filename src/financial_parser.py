from __future__ import annotations
import re
ALIASES={"assets":["자산총계","자산 총계"],"cash":["현금및현금성자산","현금및현금성자산(주석"],"receivables":["매출채권","매출채권및기타채권","매출채권및기타수취채권"],"inventory":["재고자산"],"ppe":["유형자산"],"payables":["매입채무","매입채무및기타채무","매입채무및기타지급채무"],"liabilities":["부채총계","부채 총계"],"equity":["자본총계","자본 총계"],"current_assets":["유동자산"],"current_liabilities":["유동부채"],"gross_profit":["매출총이익","매출 총이익"],"revenue":["매출액","수익(매출액)","수익","매출"],"sga":["판매비와관리비","판매비및관리비"],"operating_income":["영업이익","영업이익(손실)","영업손익"],"pretax_income":["법인세비용차감전순이익","법인세비용차감전순이익(손실)"],"income_tax_expense":["법인세비용","법인세비용(수익)"],"net_income":["당기순이익","당기순이익(손실)","분기순이익(손실)"],"attributable_net_income":["지배기업의소유주에게귀속되는당기순이익","지배주주순이익","지배기업소유주지분","지배기업 소유주지분"],"cfo":["영업활동현금흐름","영업활동으로인한현금흐름"],"cfi":["투자활동현금흐름","투자활동으로인한현금흐름"],"cff":["재무활동현금흐름","재무활동으로인한현금흐름"],"interest_expense":["이자비용","금융비용","금융원가"],"depreciation":["감가상각비"],"amortization":["무형자산상각비","무형자산상각"]}
def clean_number(v):
    if v is None:return None
    s=str(v).strip().replace(",","")
    if s in {"","-","—","N/A","nan","None"}:return None
    neg=s.startswith("(") and s.endswith(")"); s=s.strip("()")
    try:n=float(s); return -n if neg else n
    except ValueError:return None
def norm(v):return re.sub(r"\s+","",str(v or "")).lower()
def sj_matches(value,sj):
    if sj is None:return True
    if sj=="IS":return value in {"IS","CIS"}
    return value==sj
def matches(n,als):return any(norm(n)==norm(a) or norm(a) in norm(n) for a in als)
def find_row(rows,als,sj=None):
    candidates=[r for r in rows if sj_matches(r.get("sj_div"),sj)]
    for r in candidates:
        if any(norm(r.get("account_nm",""))==norm(a) for a in als): return r
    for r in candidates:
        if matches(r.get("account_nm",""),als): return r
    return None
def amount(row,cum=False):
    if not row:return None
    for k in (["thstrm_add_amount","thstrm_amount"] if cum else ["thstrm_amount","thstrm_add_amount"]):
        v=clean_number(row.get(k))
        if v is not None:return v
    return None
def pct(a,b):return None if a is None or b in (None,0) else a/b*100
def div(a,b):return None if a is None or b in (None,0) else a/b
def avg(a,b):return None if a is None or b is None else (a+b)/2
def normalize(payload,year,code,period_end=None,cumulative_flow=False):
    rows=payload.get("list",[]) or []
    def bs(k):return amount(find_row(rows,ALIASES[k],"BS"))
    def stm(k,cum=None):return amount(find_row(rows,ALIASES[k],"IS"),cumulative_flow if cum is None else cum)
    def cf(k,cum=None):return amount(find_row(rows,ALIASES[k],"CF"),cumulative_flow if cum is None else cum)
    op=stm("operating_income"); dep=cf("depreciation",cumulative_flow); am=cf("amortization",cumulative_flow)
    if dep is None:dep=amount(find_row(rows,ALIASES["depreciation"]))
    if am is None:am=amount(find_row(rows,ALIASES["amortization"]))
    ebitda=op+dep+am if op is not None and (dep is not None or am is not None) else None
    cash=bs("cash"); debt=amount(find_row(rows,["차입금","이자부차입금","차입부채"],"BS"))
    if debt is None:
        terms=["단기차입금","유동성장기차입금","장기차입금","사채","유동성사채","전환사채","신주인수권부사채"]
        vals=[amount(r) for r in rows if r.get("sj_div")=="BS" and any(matches(r.get("account_nm",""),[t]) for t in terms)]
        vals=[v for v in vals if v is not None]; debt=sum(vals) if vals else None
    terms=["유형자산의취득","유형자산취득","무형자산의취득","무형자산취득"]
    capex=sum(abs(amount(r,cumulative_flow) or 0) for r in rows if r.get("sj_div")=="CF" and any(matches(r.get("account_nm",""),[t]) for t in terms)) or None
    cfo=cf("cfo"); cfi=cf("cfi"); cff=cf("cff"); interest=stm("interest_expense")
    return {"year":year,"report_code":code,"period_end":period_end,"fs_div":payload.get("_fs_div_used"),"currency":"KRW","revenue":stm("revenue"),"gross_profit":stm("gross_profit"),"sga":stm("sga"),"operating_income":op,"pretax_income":stm("pretax_income"),"income_tax_expense":stm("income_tax_expense"),"net_income":stm("net_income"),"attributable_net_income":stm("attributable_net_income"),"ebitda":ebitda,"assets":bs("assets"),"cash":cash,"receivables":bs("receivables"),"inventory":bs("inventory"),"ppe":bs("ppe"),"payables":bs("payables"),"liabilities":bs("liabilities"),"debt":debt,"net_debt":debt-cash if debt is not None and cash is not None else None,"equity":bs("equity"),"current_assets":bs("current_assets"),"current_liabilities":bs("current_liabilities"),"cfo":cfo,"cfi":cfi,"cff":cff,"capex":capex,"fcf":cfo-capex if cfo is not None and capex is not None else None,"interest_expense":abs(interest) if interest is not None else None,"depreciation":dep,"amortization":am,"_cum":cumulative_flow}
def calculate_ratios(rows):
    out=[]; prev=None
    for r in rows:
        x=dict(r); rev=r.get("revenue"); gp=r.get("gross_profit"); op=r.get("operating_income"); ni=r.get("net_income"); assets=r.get("assets"); eq=r.get("equity"); inv=r.get("inventory"); ar=r.get("receivables"); ap=r.get("payables"); debt=r.get("debt"); nd=r.get("net_debt"); ebitda=r.get("ebitda"); cfo=r.get("cfo"); pretax=r.get("pretax_income"); tax=r.get("income_tax_expense"); interest=r.get("interest_expense")
        aa=avg(prev.get("assets") if prev else None,assets); ae=avg(prev.get("equity") if prev else None,eq); ai=avg(prev.get("inventory") if prev else None,inv); aar=avg(prev.get("receivables") if prev else None,ar); aap=avg(prev.get("payables") if prev else None,ap)
        cogs=rev-gp if rev is not None and gp is not None else None
        purchases=cogs+inv-(prev.get("inventory") if prev else None) if cogs is not None and inv is not None and prev and prev.get("inventory") is not None else None
        rate=max(0,min(1,tax/pretax)) if tax is not None and pretax not in (None,0) else .20
        nopat=op*(1-rate) if op is not None else None; invested=debt+eq-r.get("cash") if debt is not None and eq is not None and r.get("cash") is not None else None
        prev_inv=None if not prev or None in (prev.get("debt"),prev.get("equity"),prev.get("cash")) else prev["debt"]+prev["equity"]-prev["cash"]
        x.update({"cogs":cogs,"nopat":nopat,"gross_margin":pct(gp,rev),"operating_margin":pct(op,rev),"net_margin":pct(ni,rev),"ebitda_margin":pct(ebitda,rev),"roa":pct(ni,aa),"roe":pct(ni,ae),"roic":pct(nopat,avg(prev_inv,invested)),"current_ratio":div(r.get("current_assets"),r.get("current_liabilities")),"quick_ratio":div(r.get("current_assets")-inv if r.get("current_assets") is not None and inv is not None else None,r.get("current_liabilities")),"debt_ratio":pct(r.get("liabilities"),eq),"equity_ratio":pct(eq,assets),"debt_dependency":pct(debt,assets),"interest_coverage":div(op,interest),"net_debt_ebitda":div(nd,ebitda),"asset_turnover":div(rev,aa),"dso":365*aar/rev if aar is not None and rev not in (None,0) else None,"dio":365*ai/cogs if ai is not None and cogs not in (None,0) else None,"dpo":365*aap/purchases if aap is not None and purchases not in (None,0) else None,"revenue_growth":pct(rev-prev.get("revenue") if prev and rev is not None and prev.get("revenue") is not None else None,prev.get("revenue") if prev else None),"cfo_to_net_income":div(cfo,ni)})
        x["ccc"]=x["dso"]+x["dio"]-x["dpo"] if None not in (x["dso"],x["dio"],x["dpo"]) else None; x.pop("_cum",None); out.append(x); prev=x
    return out
