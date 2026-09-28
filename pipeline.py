from __future__ import annotations

import csv
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from config import CORP_CODE, CORP_NAME, END_YEAR, RAW_DIR, REPORT_CODES, REPORT_DIR, REPORT_NAMES, START_YEAR, PROCESSED_DIR, SITE_DIR, PEERS
from dart_client import DartClient
from financial_parser import ALIASES, clean_number, div, find_row, matches, calculate_ratios, extract_rows


def current_year() -> int:
    return datetime.now().year


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def build_filing_index(client: DartClient) -> List[Dict[str, Any]]:
    end_year = current_year()
    all_rows: List[Dict[str, Any]] = []
    for key, code in REPORT_CODES.items():
        rows = client.list_filings(CORP_CODE, f"{START_YEAR}0101", f"{end_year}1231", {
            "annual": "A001", "half": "A002", "quarter1": "A003", "quarter3": "A003"
        }.get(key, "A001"))
        # A003 returns both Q1 and Q3; classify by report_nm/receipt date below.
        for r in rows:
            title = r.get("report_nm", "")
            if key == "quarter1" and "1분기" not in title:
                continue
            if key == "quarter3" and "3분기" not in title:
                continue
            r["report_category"] = key
            r["report_category_name"] = REPORT_NAMES[key]
            r["dart_url"] = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r.get('rcept_no','')}"
            all_rows.append(r)

    # De-duplicate on receipt number and keep the latest entry.
    unique = {r.get("rcept_no"): r for r in all_rows if r.get("rcept_no")}
    rows = sorted(unique.values(), key=lambda r: (r.get("rcept_dt", ""), r.get("rcept_no", "")))
    save_json(RAW_DIR / "filings.json", rows)
    save_json(SITE_DIR / "data" / "filings.json", rows)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with (REPORT_DIR / "filings.csv").open("w", newline="", encoding="utf-8-sig") as f:
        cols = ["rcept_dt", "report_nm", "report_category", "rcept_no", "flr_nm", "rm", "dart_url"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return rows


def _amount(row: Dict[str, Any] | None, cumulative: bool) -> float | None:
    if not row:
        return None
    keys = ["thstrm_add_amount", "thstrm_amount"] if cumulative else ["thstrm_amount", "thstrm_add_amount"]
    for k in keys:
        n = clean_number(row.get(k))
        if n is not None:
            return n
    return None


def normalize_payload(payload: Dict[str, Any], year: int, report_code: str, cumulative: bool) -> Dict[str, Any]:
    rows = extract_rows(payload)
    def find(key: str, statement: str | None = None):
        return find_row(rows, ALIASES[key], statement)
    def val(key: str, statement: str | None = None):
        return _amount(find(key, statement), cumulative)

    revenue = val("revenue", "IS")
    gross_profit = val("gross_profit", "IS")
    op = val("operating_income", "IS")
    ni = val("net_income", "IS")
    assets = val("assets", "BS")
    cash = val("cash", "BS")
    receivables = val("receivables", "BS")
    inventory = val("inventory", "BS")
    liabilities = val("liabilities", "BS")
    equity = val("equity", "BS")
    current_assets = val("current_assets", "BS")
    current_liabilities = val("current_liabilities", "BS")
    ppe = val("ppe", "BS")
    cfo = val("cfo", "CF")
    cfi = val("cfi", "CF")
    cff = val("cff", "CF")
    interest = val("interest_expense", "IS")
    dep = val("depreciation", "IS")
    amort = val("amortization", "IS")
    ebitda = op + (dep or 0) + (amort or 0) if op is not None else None

    # CAPEX: PPE/intangible acquisition cash outflows. We store CAPEX as a positive spending amount.
    capex_terms = ["유형자산의취득", "유형자산취득", "무형자산의취득", "무형자산취득"]
    capex = 0.0
    capex_found = False
    for row in rows:
        if row.get("sj_div") != "CF":
            continue
        name = row.get("account_nm", "")
        if any(matches(name, [term]) for term in capex_terms):
            n = _amount(row, cumulative)
            if n is not None:
                capex += abs(n)
                capex_found = True
    if not capex_found:
        capex = None

    # Interest-bearing debt: prefer exact aggregate '차입금' if present; otherwise sum common components.
    debt = None
    exact_debt = find_row(rows, ["차입금", "이자부차입금", "차입부채"], "BS")
    if exact_debt:
        debt = _amount(exact_debt, cumulative)
    else:
        debt_terms = ["단기차입금", "유동성장기차입금", "장기차입금", "사채", "유동성사채", "전환사채", "신주인수권부사채"]
        vals = []
        for row in rows:
            if row.get("sj_div") == "BS" and any(matches(row.get("account_nm", ""), [t]) for t in debt_terms):
                n = _amount(row, cumulative)
                if n is not None:
                    vals.append(n)
        debt = sum(vals) if vals else None
    net_debt = debt - cash if debt is not None and cash is not None else None

    return {
        "year": year,
        "report_code": report_code,
        "fs_div": payload.get("_fs_div_used"),
        "currency": next((r.get("currency") for r in rows if r.get("currency")), None),
        "revenue": revenue, "gross_profit": gross_profit, "sga": val("sga", "IS"),
        "operating_income": op, "pretax_income": val("pretax_income", "IS"),
        "net_income": ni, "attributable_net_income": val("attributable_net_income", "IS"), "ebitda": ebitda,
        "assets": assets, "cash": cash, "receivables": receivables, "inventory": inventory,
        "ppe": ppe, "liabilities": liabilities, "debt": debt, "net_debt": net_debt, "equity": equity,
        "current_assets": current_assets, "current_liabilities": current_liabilities,
        "cfo": cfo, "cfi": cfi, "cff": cff, "capex": capex, "fcf": (cfo - capex) if cfo is not None and capex is not None else None,
        "interest_expense": interest, "depreciation": dep, "amortization": amort,
    }


def fetch_financials(client: DartClient) -> Dict[str, Any]:
    end_year = current_year()
    annual, half, q1, q3 = [], [], [], []
    raw_root = RAW_DIR / "financial"
    raw_root.mkdir(parents=True, exist_ok=True)

    for year in range(2010, end_year + 1):
        for period_key, code, target, cumulative in [
            ("annual", "11011", annual, False),
            ("half", "11012", half, True),
            ("quarter1", "11013", q1, False),
            ("quarter3", "11014", q3, False),
        ]:
            path = raw_root / f"{year}_{period_key}.json"
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
            else:
                payload = client.get_financials_with_fallback(CORP_CODE, year, code)
                save_json(path, payload)
            if str(payload.get("status")) == "000" and payload.get("list"):
                target.append(normalize_payload(payload, year, code, cumulative))

    # For quarterly values, use quarter-only figures where DART supplies them.
    # Q2 = H1 cumulative - Q1 cumulative; Q4 = annual - Q3 cumulative. For H1, store six-month cumulative separately.
    by_year = {r["year"]: r for r in half}
    q1_map = {r["year"]: r for r in q1}
    q3_map = {r["year"]: r for r in q3}
    annual_map = {r["year"]: r for r in annual}

    quarterly: List[Dict[str, Any]] = []
    fields = ["revenue", "gross_profit", "operating_income", "net_income", "ebitda", "cfo", "cfi", "cff", "capex", "fcf"]
    for year in range(2010, end_year + 1):
        if year in q1_map:
            q = dict(q1_map[year]); q["period"] = "Q1"; quarterly.append(q)
        if year in by_year and year in q1_map:
            h = by_year[year]
            q1r = q1_map[year]
            q2 = dict(h); q2["period"] = "Q2"
            for f in fields:
                a, b = h.get(f), q1r.get(f)
                q2[f] = a - b if a is not None and b is not None else None
            quarterly.append(q2)
        if year in q3_map:
            q = dict(q3_map[year]); q["period"] = "Q3"; quarterly.append(q)
        if year in annual_map and year in q3_map:
            a = annual_map[year]; q3r = q3_map[year]
            q4 = dict(a); q4["period"] = "Q4"
            for f in fields:
                aa, b = a.get(f), q3r.get(f)
                q4[f] = aa - b if aa is not None and b is not None else None
            quarterly.append(q4)

    # Annual/half tables need ratio calculations too. Quarterly stock ratios are based on same-period balance sheet figures;
    # averages are only used when a prior balance is available.
    annual_r = []
    for r in annual:
        x = dict(r); x["period"] = "Annual"; annual_r.append(x)
    half_r = []
    for r in half:
        x = dict(r); x["period"] = "Half-year"; half_r.append(x)

    output = {
        "company": CORP_NAME,
        "corp_code": CORP_CODE,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "annual": calculate_ratios(annual_r),
        "half": calculate_ratios(half_r),
        "quarterly": calculate_ratios(quarterly),
        "peers": PEERS,
        "data_note": "OpenDART 재무 API는 2015년 이후 자료를 제공합니다. 2010~2014년은 공시 목록은 수집할 수 있지만 표준 XBRL 재무수치는 API에서 제공되지 않아 공란으로 남깁니다.",
    }
    save_json(PROCESSED_DIR / "financials.json", output)
    save_json(SITE_DIR / "data" / "financials.json", output)
    return output


def write_run_status(filings: List[Dict[str, Any]], financials: Dict[str, Any]) -> None:
    status = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "filings": len(filings),
        "annual_rows": len(financials.get("annual", [])),
        "half_rows": len(financials.get("half", [])),
        "quarter_rows": len(financials.get("quarterly", [])),
        "dart_api_source": "OpenDART",
    }
    save_json(PROCESSED_DIR / "run_status.json", status)


def main() -> None:
    client = DartClient()
    filings = build_filing_index(client)
    financials = fetch_financials(client)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_run_status(filings, financials)
    print(json.dumps({"filings": len(filings), "annual": len(financials["annual"]), "half": len(financials["half"]), "quarterly": len(financials["quarterly"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
