from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA_DIR=ROOT/"data"; RAW_DIR=DATA_DIR/"raw"; RAW_FINANCIAL_DIR=RAW_DIR/"financial"; PROCESSED_DIR=DATA_DIR/"processed"; REPORT_DIR=DATA_DIR/"reports"; SITE_DATA_DIR=ROOT/"site"/"data"
CORP_CODE="00854997"; CORP_NAME="에스디바이오센서"; TICKER="137310"; START_YEAR=2010; DART_FINANCIAL_START_YEAR=2015
DART_BASE="https://opendart.fss.or.kr/api"; DART_VIEWER="https://dart.fss.or.kr/dsaf001/main.do?rcpNo="
REPORT_NAMES={"annual":"사업보고서","half":"반기보고서","quarter1":"1분기보고서","quarter3":"3분기보고서"}
PEERS=[{"name":"씨젠","ticker":"096530","focus":"분자진단(PCR)","note":"분자진단"},{"name":"바디텍메드","ticker":"206640","focus":"면역진단","note":"면역진단"},{"name":"수젠텍","ticker":"253840","focus":"면역·현장진단","note":"면역·현장진단"},{"name":"휴마시스","ticker":"205470","focus":"현장진단","note":"신속진단"},{"name":"오상헬스케어","ticker":"036220","focus":"체외진단","note":"혈당·면역·분자진단"},{"name":"엑세스바이오","ticker":"950130","focus":"현장진단","note":"글로벌 신속진단"}]
FLOW_FIELDS=["revenue","gross_profit","sga","operating_income","pretax_income","income_tax_expense","net_income","attributable_net_income","ebitda","cfo","cfi","cff","capex","fcf","interest_expense","depreciation","amortization"]
