# HN_SD.BIO — SD Biosensor OpenDART Financial Agent

[![🔗 대시보드 바로가기](https://hsc-class02.github.io/HN_SD.BIO/assets/dashboard-badge.svg)](https://hsc-class02.github.io/HN_SD.BIO/)

에스디바이오센서(종목코드 **137310**, DART 고유번호 **00854997**)의 사업보고서·반기보고서·분기보고서를 OpenDART API로 수집하고, 주요 재무수치와 재무비율을 계산하여 GitHub Pages Dashboard로 제공합니다.

## Dashboard

**https://hsc-class02.github.io/HN_SD.BIO/**

**흐름:** OpenDART → Python Agent → Raw JSON → 정규화/재무비율 분석 → GitHub commit → GitHub Pages

## 자동화 설정

| 항목 | 설정 |
|---|---|
| 대상 기업 | 에스디바이오센서 (137310) |
| 보고서 | 사업보고서 · 반기보고서 · 1분기보고서 · 3분기보고서 |
| 요청 시작연도 | 2010 |
| 표준 재무수치 | OpenDART fnlttSinglAcntAll, 2015년 이후 |
| 업데이트 | 매월 1일 09:00 KST |
| Cron | 0 0 1 * * (UTC) |
| 실행 | GitHub Actions |
| Dashboard | GitHub Pages |

## 주요 재무수치

첨부된 「재무제표 및 재무비율 실무 가이드」의 범주를 반영하여 다음 수치를 추출합니다. fileciteturn1file6

**재무상태표:** 총자산, 현금및현금성자산, 매출채권, 재고자산, 유형자산, 매입채무, 총부채, 이자부차입금, 순차입금, 자본총계, 유동자산, 유동부채

**손익계산서:** 매출액, 매출총이익, 판매비와관리비, 영업이익, 세전이익, 당기순이익, 지배주주순이익, EBITDA

**현금흐름표:** 영업활동현금흐름(CFO), 투자활동현금흐름(CFI), 재무활동현금흐름(CFF), CAPEX, FCF

## 재무비율

매출총이익률, 영업이익률, 순이익률, EBITDA Margin, ROA, ROE, ROIC, 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, DPO, CCC, 매출증가율, CFO/순이익을 계산합니다. fileciteturn1file5

ROIC는 재무제표에서 추정한 분석지표이며 회사가 공시하는 KPI와 동일하지 않을 수 있습니다. DPO/CCC는 필요한 매입·재고·매입채무 이력이 확보되는 경우 계산합니다.

## 2010년부터의 데이터

요청 시작연도는 2010년입니다. 다만 OpenDART 표준 단일회사 전체 재무제표 API는 2015년 이후 정보를 제공합니다. 따라서 agent는 2010–2014년 숫자를 임의로 생성하지 않고 해당 기간을 **legacy parser 대상**으로 표시합니다. citeturn536717search0

2010–2014년의 실제 수치까지 완성하려면 DART 원문 과거보고서의 별도 legacy parser를 추가해야 합니다. 현재 버전은 데이터의 신뢰성을 위해 빈 값을 그대로 유지합니다.

## API Key

**Settings → Secrets and variables → Actions → New repository secret**

- Name: DART_API_KEY
- Secret: OpenDART에서 발급받은 인증키

인증키는 코드나 README에 저장하지 않습니다.

## 최초 실행 / 오류 점검

1. GitHub → **Actions**
2. **DART Financial Agent**
3. **Run workflow**
4. main 선택 후 실행

Workflow에는 Python compile/test 단계가 먼저 실행되며, 이후 DART API 수집 → 데이터 저장 → Pages 배포가 이어집니다.

## Dashboard 구성

상단: 매출·영업이익·순이익 추이, 이익률 추이, 현금·차입금·순차입금, CFO·FCF

하단: **Annual**, **Half-year**, **Quarterly**, **국내 Peer Firms** tables

## 국내 Peer Firms

| 기업 | 종목코드 | 주요 영역 | 비고 |
|---|---:|---|---|
| 씨젠 | 096530 | 분자진단(PCR) | 분자진단 |
| 바디텍메드 | 206640 | 면역진단 | 면역진단 |
| 수젠텍 | 253840 | 면역·현장진단 | 면역·현장진단 |
| 휴마시스 | 205470 | 현장진단 | 신속진단 |
| 오상헬스케어 | 036220 | 체외진단 | 혈당·면역·분자진단 |
| 엑세스바이오 | 950130 | 현장진단 | 글로벌 신속진단 |

Peer group은 국내 체외진단 산업의 참고군입니다. 우열이나 투자등급을 의미하지 않습니다.

## GitHub Pages / About

Pages: https://hsc-class02.github.io/HN_SD.BIO/

저장소 오른쪽 **About → Edit → Website**에 위 Dashboard 주소를 입력하면 repository 메인 화면에서 바로 이동할 수 있습니다.

GitHub connector에서는 repository About의 Website 설정을 직접 변경하는 관리 API가 제공되지 않아, **About의 Website 입력만 GitHub 화면에서 1회 수동 설정**이 필요합니다.

## Repository 구조

.github/workflows/dart-agent.yml
src/config.py
src/dart_client.py
src/financial_parser.py
src/pipeline.py
tests/
data/raw/
data/processed/
data/reports/
site/index.html
site/assets/dashboard-badge.svg
site/data/
requirements.txt
README.md

## 로컬 테스트

python -m unittest discover -s tests -p test_*.py -v
python src/pipeline.py

재무수치는 원문 DART 보고서와 함께 교차검증하는 것을 권장합니다.
