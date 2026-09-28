[업로드용 ZIP 안내]

이 ZIP에는 업로드를 방해하는 숨김 파일/폴더(.DS_Store 등)를 넣지 않았습니다.

중요: GitHub Actions는 최종적으로 `.github/workflows/dart-agent.yml` 경로를 요구합니다.
ZIP에서는 숨김 폴더를 피하기 위해 `github/workflows/dart-agent.yml`로 넣었습니다.

GitHub 웹에서:
1) 저장소에 `github/workflows/dart-agent.yml` 파일을 업로드
2) 업로드 후 파일 경로를 `.github/workflows/dart-agent.yml`로 생성하도록 GitHub의 Add file → Create new file에서 내용을 복사하거나,
   로컬 Git 사용 시 `github/workflows/dart-agent.yml`을 `.github/workflows/dart-agent.yml`로 이동
3) Settings → Secrets and variables → Actions → DART_API_KEY 등록
4) Settings → Pages → Source = GitHub Actions
5) Actions → DART Financial Agent → Run workflow

GitHub Pages 주소:
https://naena0815-maker.github.io/HN_SD.BIO/
