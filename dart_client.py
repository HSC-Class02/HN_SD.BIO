import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from config import DART_BASE


class DartAPIError(RuntimeError):
    pass


class DartClient:
    def __init__(self, api_key: Optional[str] = None, timeout: int = 30, sleep_seconds: float = 0.2):
        self.api_key = api_key or os.getenv("DART_API_KEY")
        if not self.api_key:
            raise DartAPIError("DART_API_KEY가 없습니다. GitHub Actions Secret 또는 환경변수로 설정하세요.")
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "HN_SD_BIO-DART-Agent/1.0"})

    def get_json(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params = {**params, "crtfc_key": self.api_key}
        url = f"{DART_BASE}/{endpoint}.json"
        last_error = None
        for attempt in range(3):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                r.raise_for_status()
                data = r.json()
                status = str(data.get("status", ""))
                if status != "000":
                    # 013 is an expected 'no data' response and is handled by callers.
                    if status == "013":
                        return data
                    raise DartAPIError(f"OpenDART {endpoint}: {status} {data.get('message', '')}")
                return data
            except (requests.RequestException, ValueError, DartAPIError) as exc:
                last_error = exc
                if isinstance(exc, DartAPIError) and "013" not in str(exc):
                    raise
                time.sleep(1.5 ** attempt)
        raise DartAPIError(f"OpenDART 요청 실패: {endpoint}: {last_error}")

    def list_filings(self, corp_code: str, start_date: str, end_date: str, detail_code: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        page = 1
        while True:
            data = self.get_json(
                "list",
                {
                    "corp_code": corp_code,
                    "bgn_de": start_date,
                    "end_de": end_date,
                    "pblntf_ty": "A",
                    "pblntf_detail_ty": detail_code,
                    "last_reprt_at": "Y",
                    "page_no": page,
                    "page_count": 100,
                },
            )
            batch = data.get("list", []) or []
            rows.extend(batch)
            total_page = int(data.get("total_page", 1) or 1)
            if page >= total_page or not batch:
                break
            page += 1
            time.sleep(self.sleep_seconds)
        return rows

    def get_financials(self, corp_code: str, bsns_year: int, reprt_code: str, fs_div: str) -> Dict[str, Any]:
        return self.get_json(
            "fnlttSinglAcntAll",
            {
                "corp_code": corp_code,
                "bsns_year": str(bsns_year),
                "reprt_code": reprt_code,
                "fs_div": fs_div,
            },
        )

    def get_financials_with_fallback(self, corp_code: str, bsns_year: int, reprt_code: str) -> Dict[str, Any]:
        for fs_div in ("CFS", "OFS"):
            data = self.get_financials(corp_code, bsns_year, reprt_code, fs_div)
            if str(data.get("status")) == "000" and data.get("list"):
                data["_fs_div_used"] = fs_div
                return data
        return {"status": "013", "message": "조회된 재무제표가 없습니다.", "list": []}

    @staticmethod
    def save_json(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
