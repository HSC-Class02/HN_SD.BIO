# HN_SD.BIO — SD Biosensor OpenDART Financial Agent

[![🔗 대시보드 바로가기](site/assets/dashboard-badge.svg)](https://naena0815-maker.github.io/HN_SD.BIO/)

에스디바이오센서(종목코드 137310, DART 고유번호 00854997)의 **사업보고서·반기보고서·분기보고서**를 OpenDART API로 자동 수집하고, 주요 재무수치와 재무비율을 계산하여 GitHub Pages Dashboard에 게시하는 프로젝트입니다.

> **핵심 흐름**: OpenDART → Python Agent → JSON/CSV → GitHub commit → GitHub Pages Dashboard

## 1. 포함 기능

- 2010년부터 현재까지 정기보고서 공시 목록 수집
- 사업보고서(A001), 반기보고서(A002), 분기보고서(A003) 수집
- 2015년 이후 OpenDART XBRL 재무수치 자동 수집
- 연결재무제표(CFS) 우선, 없으면 별도재무제표(OFS) fallback
- Annual / Half-year / Quarterly 3개 테이블
- 매출, 매출총이익, 판관비, 영업이익, 세전이익, 순이익, 지배주주순이익, EBITDA, 자산, 현금, 매출채권, 재고, 유형자산, 부채, 이자부차입금, 자본, CFO/CFI/CFF, CAPEX, FCF, 순차입금 등
- 매출총이익률, 영업이익률, 순이익률, EBITDA margin, ROA, ROE, 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA, 총자산회전율, DSO, DIO, 매출증가율, CFO/순이익 등 자동 계산
- Q2 = 반기 누적 − Q1, Q4 = 연간 − Q3 방식으로 분기값 산출
- 국내 peer firms table
- GitHub Actions 월 1회 자동 실행 + 수동 실행 가능
- GitHub Pages 자동 배포

## 2. 중요: 2010~2014년 데이터 범위

OpenDART의 `fnlttSinglAcntAll` 표준 XBRL 재무제표 API는 **2015년 이후** 정보를 제공합니다. 따라서 이 프로젝트는 2010년부터 DART 정기보고서 **공시 목록/원문 링크 메타데이터**를 수집하지만, 표준 재무수치는 2015년 이후부터 자동 추출합니다.

2010~2014년 재무수치를 별도로 채우려면 DART 원문 보고서의 과거 재무제표를 추가 파싱하는 별도 legacy parser가 필요합니다. 현재 버전은 없는 숫자를 임의로 채우지 않습니다.

## 3. GitHub Actions Secret 설정

GitHub 저장소에서:

**Settings → Secrets and variables → Actions → New repository secret**

- Name: `DART_API_KEY`
- Secret: OpenDART에서 발급받은 40자리 인증키

**API 키를 README, Python 코드, GitHub Actions YAML에 직접 입력하지 마세요.**

## 4. 최초 실행

GitHub Actions → `DART Financial Agent` → **Run workflow**

최초 실행에서는 2010년부터 현재까지의 공시 목록을 만들고, 2015년 이후 재무 API를 조회합니다.

이후 생성되는 주요 파일:

- `data/raw/filings.json` — DART 공시 목록
- `data/reports/filings.csv` — 보고서 목록 + DART 원문 링크
- `data/raw/financial/*.json` — 연도/보고서별 OpenDART 원자료
- `data/processed/financials.json` — 대시보드용 정규화 데이터
- `site/data/financials.json` — GitHub Pages가 읽는 데이터

## 5. 자동 업데이트

GitHub Actions는 매월 **1일 09:00 KST**에 실행되도록 설정되어 있습니다.

- Cron: `0 0 1 * *` (UTC)
- 수동 실행: `workflow_dispatch`
- 코드 변경 시에도 실행: `push`

새 보고서가 DART에 추가되면 다음 실행 때 공시 목록과 재무 데이터가 갱신되고, 변경분이 GitHub에 커밋됩니다.

## 6. Dashboard

GitHub Pages 주소:

**https://naena0815-maker.github.io/HN_SD.BIO/**

저장소 README 최상단의 배지와 Dashboard 링크는 이 주소를 가리킵니다.

## 7. GitHub About 링크

저장소의 오른쪽 **About → Edit**에서 Website에 아래 주소를 입력하세요.

`https://naena0815-maker.github.io/HN_SD.BIO/`

About 영역은 저장소 소유자 권한이 필요하므로, GitHub 연결이 완료되면 자동 설정할 수 있습니다.

## 8. 재무분석 기준

첨부된 「재무제표 및 재무비율 실무 가이드」의 구조를 기준으로 성장성 → 수익성 → 현금흐름 → 차입부담 → 자본효율의 흐름으로 지표를 구성했습니다.

단일 비율만 보지 않고 금액과 비율을 함께 보고, 연결/별도 및 기간 기준을 섞지 않는 것을 기본 원칙으로 합니다.

## 9. Peer firms

국내 체외진단 관련 참고군으로 다음 기업을 표시합니다.

| 기업 | 종목코드 | 주요 영역 | 참고 |
|---|---:|---|---|
| 씨젠 | 096530 | 분자진단(PCR) | 국내 주요 분자진단 기업 |
| 바디텍메드 | 206640 | 면역진단 | 형광면역진단 장비·키트 |
| 수젠텍 | 253840 | 면역·현장진단 | 여성호르몬·면역진단 등 |
| 휴마시스 | 205470 | 현장진단 | 신속진단 중심 |
| 엑세스바이오 | 950130 | 현장진단 | 글로벌 신속진단 |
| 오상헬스케어 | 036220 | 체외진단 | 혈당·면역·분자진단 |

Peer 표는 국내 체외진단 산업 자료를 참고한 분류이며, 우열이나 투자등급을 의미하지 않습니다.

## 10. 로컬 테스트

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 환경변수 설정 후
python src/pipeline.py
```

브라우저에서 `site/index.html`을 정적 서버로 열어 확인할 수 있습니다.

## 11. 파일 구조

```text
HN_SD.BIO/
├── .github/workflows/dart-agent.yml
├── src/
│   ├── config.py
│   ├── dart_client.py
│   ├── financial_parser.py
│   └── pipeline.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── site/
│   ├── index.html
│   ├── assets/
│   └── data/
├── requirements.txt
├── config.example.env
└── README.md
```
