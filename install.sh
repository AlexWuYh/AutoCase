#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v pipx >/dev/null 2>&1; then
  echo "[autocase] Using pipx for system-level install"
  pipx install "$ROOT_DIR" --force
  exit 0
fi

if command -v brew >/dev/null 2>&1; then
  echo "[autocase] pipx not found, installing via Homebrew"
  brew install pipx
  pipx ensurepath
  pipx install "$ROOT_DIR" --force
  exit 0
fi

if command -v apt >/dev/null 2>&1; then
  echo "[autocase] pipx not found, installing via apt"
  sudo apt update
  sudo apt install -y pipx
  pipx ensurepath
  pipx install "$ROOT_DIR" --force
  exit 0
fi

echo "[autocase] pipx/brew/apt not found."
echo "Please install pipx manually, then run: pipx install ."
exit 1
