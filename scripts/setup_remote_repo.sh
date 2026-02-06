#!/usr/bin/env bash
set -euo pipefail

REMOTE_NAME="${1:-origin}"
RAW_REMOTE_URL="${2:-https://github.com/matverse-acoa/papers.git}"

normalize_remote_url() {
  local raw="$1"

  # Suporta URL web do GitHub (com ou sem .git)
  if [[ "$raw" =~ ^https://github.com/([^/]+)/([^/]+)/?$ ]]; then
    echo "https://github.com/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}.git"
    return
  fi
  if [[ "$raw" =~ ^https://github.com/([^/]+)/([^/]+)\.git$ ]]; then
    echo "$raw"
    return
  fi

  # Suporta SSH canonical já pronto
  if [[ "$raw" =~ ^git@github.com:[^/]+/[^/]+(\.git)?$ ]]; then
    if [[ "$raw" != *.git ]]; then
      echo "${raw}.git"
    else
      echo "$raw"
    fi
    return
  fi

  # Fallback: usa como informado
  echo "$raw"
}

REMOTE_URL="$(normalize_remote_url "$RAW_REMOTE_URL")"

if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  git remote set-url "$REMOTE_NAME" "$REMOTE_URL"
  echo "Updated remote '$REMOTE_NAME' -> $REMOTE_URL"
else
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
  echo "Added remote '$REMOTE_NAME' -> $REMOTE_URL"
fi

git remote -v

echo "\nConnectivity check (non-fatal):"
if [[ "$REMOTE_URL" == git@github.com:* ]]; then
  if command -v timeout >/dev/null 2>&1; then
    timeout 5 ssh -o BatchMode=yes -T git@github.com 2>&1 | sed -n '1,3p' || true
  else
    ssh -o BatchMode=yes -T git@github.com 2>&1 | sed -n '1,3p' || true
  fi
else
  echo "HTTPS remote configured (no SSH check required)."
fi
