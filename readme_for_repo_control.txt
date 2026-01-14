  방법 1: 로컬 브랜치 방식 (간단)

  cd py-clob-client

  # 내 수정용 브랜치 생성
  git checkout -b factec-custom

  # 여기서 수정 작업 진행...
  # 커밋도 이 브랜치에

  # 원본 업데이트 받을 때:
  git checkout main
  git pull origin main
  git checkout factec-custom
  git merge main  # 또는 git rebase main

  방법 2: Fork + Upstream 방식 (추천) ← 현재 사용중

  장기적으로 더 깔끔합니다.

  1. GitHub에서 Polymarket/py-clob-client를 Fork
  2. 아래처럼 remote 설정:

  cd py-clob-client

  # origin을 내 fork로 변경
  git remote set-url origin https://github.com/ryanly-fac/py-clob-client-factec.git

  # 원본을 upstream으로 추가
  git remote add upstream https://github.com/Polymarket/py-clob-client.git

  # 내 수정 브랜치 생성 및 작업
  git checkout -b factec-custom
  # ... 수정 ...
  git push origin factec-custom

  # 원본 업데이트 받을 때:
  git fetch upstream
  git checkout main
  git merge upstream/main
  git checkout factec-custom
  git merge main

# 원본 업데이트 자동화
./sync-upstream.sh 실행