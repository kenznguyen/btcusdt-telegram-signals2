#!/usr/bin/env bash
set -euo pipefail

: "${CM_BUILD_DIR:?Codemagic checkout directory is required}"
: "${CM_ENV:?Codemagic environment file is required}"
cd "$CM_BUILD_DIR"
git rev-parse HEAD | tee ci-source-sha.txt
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10+ required"'
python3 -m venv "$CM_BUILD_DIR/.ci-tools/python-venv"
ci_python="$CM_BUILD_DIR/.ci-tools/python-venv/bin/python"
export PIP_CACHE_DIR="$HOME/.cache/pip"
requirements=()
for requirement in "$@"; do
  requirements+=(-r "$requirement")
done
"$ci_python" -m pip install "${requirements[@]}"
printf 'CI_PYTHON=%s\n' "$ci_python" >> "$CM_ENV"
