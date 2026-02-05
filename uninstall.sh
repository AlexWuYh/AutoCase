#!/usr/bin/env bash
set -euo pipefail

if command -v pipx >/dev/null 2>&1; then
  echo "[autocase] Uninstalling via pipx"
  pipx uninstall autocase
  exit 0
fi

echo "[autocase] pipx not found. If you installed via pip, run: pip3 uninstall autocase"
exit 1
