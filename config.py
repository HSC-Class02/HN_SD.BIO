from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORT_DIR = DATA_DIR / "reports"
SITE_DIR = ROOT / "site"

CORP_CODE = "00854997"
CORP_NAME = "에스디바이오센서"
START_YEAR = 2010
END_YEAR = 2099
DART_BASE = "https://opendart.fss.or.kr/api"
DART_VIEWER = "https://dart.fss.or.kr/dsaf001/main.do?rcpNo="

REPORT_CODES = {
    "annual": "11011",
    "half": "11012",
    "quarter1": "11013",
    "quarter3": "11014",
}

REPORT_NAMES = {
    "annual": "사업보고서",
    "half": "반기보고서",
    "quarter1": "1분기보고서",
    "quarter3": "3분기보고서",
}

PEERS = [
    {"name": "씨젠", "ticker": "096530", "focus": "분자진단(PCR)", "note": "국내 주요 분자진단 기업"},
    {"name": "바디텍메드", "ticker": "206640", "focus": "면역진단", "note": "형광면역진단 장비·키트"},
    {"name": "수젠텍", "ticker": "253840", "focus": "면역·현장진단", "note": "여성호르몬·면역진단 등"},
    {"name": "휴마시스", "ticker": "205470", "focus": "현장진단", "note": "신속진단 중심"},
    {"name": "엑세스바이오", "ticker": "950130", "focus": "현장진단", "note": "글로벌 신속진단"},
    {"name": "오상헬스케어", "ticker": "036220", "focus": "체외진단", "note": "혈당·면역·분자진단"},
]
