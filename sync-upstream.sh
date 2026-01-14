#!/bin/bash

# 원본(Polymarket) 업데이트를 받아서 factec-custom 브랜치에 머지하는 스크립트

set -e

echo "==> Fetching upstream..."
git fetch upstream

echo "==> Updating main from upstream..."
git checkout main
git merge upstream/main

echo "==> Pushing main to origin..."
git push origin main

echo "==> Merging main into factec-custom..."
git checkout factec-custom
git merge main

echo "==> Done! Now on factec-custom branch with latest upstream changes."
