from __future__ import annotations

import math
import re
from typing import Any, Dict, Iterable, List, Optional


def clean_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip().replace(",", "")
    if s in {"", "-", "—", "N/A", "nan", "None"}:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        n = float(s)
        return -n if neg else n
    except ValueError:
        return None


def norm(s: Any) -> str:
    return re.sub(r"\s+", "", str(s or "")).lower()


def matches(name: str, aliases: Iterable[str]) -> bool:
    n = norm(name)
    return any(norm(a) == n or norm(a) in n for a in aliases)


ALIASES = {
    "assets": ["자산총계", "자산 총계"],
    "cash": ["현금및현금성자산", "현금및현금성자산", "현금및현금성자산(주석"],
    "receivables": ["매출채권", "매출채권및기타채권"],
    "inventory": ["재고자산"],
    "ppe": ["유형자산"],
    "liabilities": ["부채총계"],
    "equity": ["자본총계"],
    "current_assets": ["유동자산"],
    "current_liabilities": ["유동부채"],
    "gross_profit": ["매출총이익"],
    "revenue": ["매출액", "수익(매출액)", "수익"],
    "sga": ["판매비와관리비", "판매비및관리비"],
    "operating_income": ["영업이익", "영업이익(손실)"],
    "pretax_income": ["법인세비용차감전순이익", "법인세비용차감전순이익(손실)", "세전이익"],
    "net_income": ["당기순이익", "당기순이익(손실)"],
    "attributable_net_income": ["지배기업의소유주에게귀속되는당기순이익", "지배기업소유주지분순이익", "지배기업의소유주지분"],
    "cfo": ["영업활동현금흐름", "영업활동으로인한현금흐름"],
    "cfi": ["투자활동현금흐름", "투자활동으로인한현금흐름"],
    "cff": ["재무활동현금흐름", "재무활동으로인한현금흐름"],
    "interest_expense": ["이자비용", "금융비용"],
    "depreciation": ["감가상각비"],
    "amortization": ["무형자산상각비", "상각비"],
}


def extract_rows(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return payload.get("list", []) or []


def find_row(rows: List[Dict[str, Any]], aliases: Iterable[str], statement: Optional[str] = None) -> Optional[Dict[str, Any]]:
    candidates = rows
    if statement:
        candidates = [r for r in rows if r.get("sj_div") == statement] or rows
    for row in candidates:
        if matches(row.get("account_nm", ""), aliases):
            return row
    return None


def pick_amount(row: Optional[Dict[str, Any]], cumulative: bool = False) -> Optional[float]:
    if not row:
        return None
    keys = ["thstrm_add_amount", "thstrm_amount"] if cumulative else ["thstrm_amount", "thstrm_add_amount"]
    for key in keys:
        n = clean_number(row.get(key))
        if n is not None:
            return n
    return None


def pick_prior_amount(row: Optional[Dict[str, Any]], cumulative: bool = False) -> Optional[float]:
    if not row:
        return None
    keys = ["frmtrm_add_amount", "frmtrm_amount"] if cumulative else ["frmtrm_amount", "frmtrm_add_amount"]
    for key in keys:
        n = clean_number(row.get(key))
        if n is not None:
            return n
    return None


def avg(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return (a + b) / 2


def div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return a / b


def safe_pct(a: Optional[float], b: Optional[float]) -> Optional[float]:
    x = div(a, b)
    return x * 100 if x is not None else None


def normalize_financial_payload(payload: Dict[str, Any], year: int, report_code: str) -> Dict[str, Any]:
    rows = extract_rows(payload)
    bs = lambda key: pick_amount(find_row(rows, ALIASES[key], "BS"))
    is_ = lambda key: pick_amount(find_row(rows, ALIASES[key], "IS"))
    cf = lambda key: pick_amount(find_row(rows, ALIASES[key], "CF"))

    revenue = is_("revenue")
    gross_profit = is_("gross_profit")
    operating_income = is_("operating_income")
    net_income = is_("net_income")
    assets = bs("assets")
    liabilities = bs("liabilities")
    equity = bs("equity")
    current_assets = bs("current_assets")
    current_liabilities = bs("current_liabilities")
    cash = bs("cash")
    receivables = bs("receivables")
    inventory = bs("inventory")
    ppe = bs("ppe")
    cfo = cf("cfo")
    cfi = cf("cfi")
    cff = cf("cff")
    interest = is_("interest_expense")
    depreciation = is_("depreciation")
    amortization = is_("amortization")
    ebitda = None if operating_income is None else operating_income + (depreciation or 0) + (amortization or 0)

    # Debt: use explicit current/non-current borrowings when available; otherwise leave blank rather than treating total liabilities as debt.
    debt_aliases = [
        "단기차입금", "유동성장기차입금", "장기차입금", "사채", "전환사채", "신주인수권부사채",
        "유동성사채", "장기차입부채", "유동성장기부채",
    ]
    debt_rows = [r for r in rows if r.get("sj_div") == "BS" and matches(r.get("account_nm", ""), debt_aliases)]
    debt = sum((pick_amount(r) or 0) for r in debt_rows) if debt_rows else None
    net_debt = (debt - cash) if debt is not None and cash is not None else None

    return {
        "year": year,
        "report_code": report_code,
        "fs_div": payload.get("_fs_div_used"),
        "currency": next((r.get("currency") for r in rows if r.get("currency")), None),
        "revenue": revenue,
        "gross_profit": gross_profit,
        "sga": is_("sga"),
        "operating_income": operating_income,
        "pretax_income": is_("pretax_income"),
        "net_income": net_income,
        "attributable_net_income": is_("attributable_net_income"),
        "ebitda": ebitda,
        "assets": assets,
        "cash": cash,
        "receivables": receivables,
        "inventory": inventory,
        "ppe": ppe,
        "liabilities": liabilities,
        "debt": debt,
        "net_debt": net_debt,
        "equity": equity,
        "current_assets": current_assets,
        "current_liabilities": current_liabilities,
        "cfo": cfo,
        "cfi": cfi,
        "cff": cff,
        "capex": None,
        "fcf": None,
        "interest_expense": interest,
        "depreciation": depreciation,
        "amortization": amortization,
    }


def derive_periods(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # The API returns 3-month values in thstrm_amount and cumulative values in thstrm_add_amount for interim income statements.
    # This function standardizes the records while preserving the raw annual/half/quarter API outputs.
    out: List[Dict[str, Any]] = []
    for r in records:
        code = r.get("report_code")
        period = {"annual": "annual", "half": "half", "quarter1": "Q1", "quarter3": "Q3"}.get(code, code)
        x = dict(r)
        x["period"] = period
        out.append(x)
    return out


def calculate_ratios(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Rows must be sorted by period end. For stock items, previous period is used for averages.
    rows = sorted(rows, key=lambda x: (x.get("year", 0), x.get("period", "")))
    result = []
    previous = None
    for r in rows:
        x = dict(r)
        revenue = r.get("revenue")
        assets = r.get("assets")
        equity = r.get("equity")
        current_assets = r.get("current_assets")
        current_liabilities = r.get("current_liabilities")
        debt = r.get("debt")
        net_debt = r.get("net_debt")
        gross_profit = r.get("gross_profit")
        op = r.get("operating_income")
        ni = r.get("net_income")
        ebitda = r.get("ebitda")
        cfo = r.get("cfo")
        inventory = r.get("inventory")
        receivables = r.get("receivables")
        interest = r.get("interest_expense")

        avg_assets = avg(previous.get("assets") if previous else None, assets)
        avg_equity = avg(previous.get("equity") if previous else None, equity)
        avg_inventory = avg(previous.get("inventory") if previous else None, inventory)
        avg_receivables = avg(previous.get("receivables") if previous else None, receivables)

        x["gross_margin"] = safe_pct(gross_profit, revenue)
        x["operating_margin"] = safe_pct(op, revenue)
        x["net_margin"] = safe_pct(ni, revenue)
        x["ebitda_margin"] = safe_pct(ebitda, revenue)
        x["roa"] = safe_pct(ni, avg_assets)
        x["roe"] = safe_pct(ni, avg_equity)
        x["roic"] = None  # requires a defined NOPAT/tax and invested-capital policy; kept blank rather than inventing adjustments.
        x["current_ratio"] = div(current_assets, current_liabilities)
        x["quick_ratio"] = div((current_assets - inventory) if current_assets is not None and inventory is not None else None, current_liabilities)
        x["debt_ratio"] = safe_pct(r.get("liabilities"), equity)
        x["equity_ratio"] = safe_pct(equity, assets)
        x["debt_dependency"] = safe_pct(debt, assets)
        x["interest_coverage"] = div(op, interest)
        x["net_debt_ebitda"] = div(net_debt, ebitda)
        x["asset_turnover"] = div(revenue, avg_assets)
        x["receivables_turnover"] = div(revenue, avg_receivables)
        x["dso"] = div(365, x["receivables_turnover"])
        x["inventory_turnover"] = div(revenue, avg_inventory)
        x["dio"] = div(365, x["inventory_turnover"])
        x["dpo"] = None  # requires purchases/credit purchases, which is not consistently available as a standardized XBRL account.
        x["ccc"] = None
        x["revenue_growth"] = safe_pct((revenue - previous.get("revenue")) if previous and revenue is not None and previous.get("revenue") is not None else None, previous.get("revenue") if previous else None)
        x["cfo_to_net_income"] = div(cfo, ni)
        x["fcf"] = (cfo - r.get("capex")) if cfo is not None and r.get("capex") is not None else None
        result.append(x)
        previous = r
    return result
