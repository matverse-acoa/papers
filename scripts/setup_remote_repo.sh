#!/usr/bin/env bash
set -euo pipefail

REMOTE_NAME="${1:-origin}"
REMOTE_URL="${2:-git@github.com:matverse-acoa/papers.git}"

if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git remote set-url "$REMOTE_NAME" "$REMOTE_URL"
  echo "Updated remote '$REMOTE_NAME' -> $REMOTE_URL"
else
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
  echo "Added remote '$REMOTE_NAME' -> $REMOTE_URL"
fi

git remote -v

echo "\nTesting SSH access (non-fatal if key not configured)..."
if command -v timeout >/dev/null 2>&1; then
  timeout 5 ssh -o BatchMode=yes -T git@github.com 2>&1 | sed -n '1,3p' || true
else
  ssh -o BatchMode=yes -T git@github.com 2>&1 | sed -n '1,3p' || true
fi
