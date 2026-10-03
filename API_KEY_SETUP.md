# OpenDART API 키 입력 방법

## 1. OpenDART에서 인증키 발급

OpenDART: https://opendart.fss.or.kr/

회원가입/로그인 후 Open API 인증키를 발급받습니다.

## 2. GitHub에 Secret으로 등록

저장소:
`https://github.com/HSC-Class02/HN_SD.BIO`

경로:

**Settings → Secrets and variables → Actions → New repository secret**

입력:

- Name: `DART_API_KEY`
- Secret: 발급받은 40자리 인증키

저장 후 Python 코드에서는 아래처럼 사용됩니다.

```python
import os
api_key = os.environ["DART_API_KEY"]
```

`src/dart_client.py`가 실제 API 호출을 담당하므로 API 키를 소스코드에 하드코딩할 필요가 없습니다.

## 3. 로컬에서 테스트할 때

Windows PowerShell:

```powershell
$env:DART_API_KEY="발급받은40자리키"
python src/pipeline.py
```

macOS/Linux:

```bash
export DART_API_KEY="발급받은40자리키"
python src/pipeline.py
```

## 4. GitHub Actions 수동 테스트

1. Actions 탭
2. `DART Financial Agent` 선택
3. `Run workflow`
4. `main` 선택
5. 실행

## 5. 절대 하면 안 되는 것

아래처럼 API 키를 코드에 직접 넣지 마세요.

```python
# 금지
api_key = "실제_인증키"
```

API 키가 커밋되었다면 즉시 OpenDART에서 해당 키를 폐기/재발급하고 GitHub에 새 Secret으로 등록하세요.
