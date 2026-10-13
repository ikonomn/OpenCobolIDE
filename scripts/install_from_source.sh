#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
venv_dir="${OCIDE_VENV_DIR:-$repo_dir/.venv}"
python_command="${PYTHON:-python3}"

if ! command -v "$python_command" >/dev/null 2>&1; then
    echo "Python was not found: $python_command" >&2
    exit 1
fi

"$python_command" -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install --upgrade pip setuptools wheel
"$venv_dir/bin/python" -m pip install "$repo_dir"

echo
echo "OpenCobolIDE was installed in: $venv_dir"
echo "Run it with: $venv_dir/bin/opencobolide"
if ! command -v cobc >/dev/null 2>&1; then
    echo
    echo "Warning: cobc was not found in PATH. Install GnuCOBOL before compiling."
fi
