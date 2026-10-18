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

# Optional user-level launcher; no system Python or sudo required.
if [[ ${OCIDE_INSTALL_LAUNCHER:-0} == 1 ]]; then
    launcher_dir="${OCIDE_LAUNCHER_DIR:-$HOME/.local/bin}"
    mkdir -p "$launcher_dir"
    launcher="$launcher_dir/opencobolide"
    marker='# OpenCobolIDE source-install launcher'
    if [[ -e "$launcher" || -L "$launcher" ]]; then
        if [[ -L "$launcher" ]] || ! grep -qF "$marker" "$launcher"; then
            echo "Launcher already exists and was not replaced: $launcher" >&2
            exit 1
        fi
    fi
    # Python quotes arbitrary installation paths safely for a POSIX shell.
    "$venv_dir/bin/python" - "$launcher" "$venv_dir/bin/opencobolide" <<'PYLAUNCH'
import shlex
import sys
from pathlib import Path
p = Path(sys.argv[1])
p.write_text('#!/bin/sh\n# OpenCobolIDE source-install launcher\nexec ' +
             shlex.quote(sys.argv[2]) + ' "$@"\n')
p.chmod(0o755)
PYLAUNCH
    echo "Launcher installed: $launcher"
    echo "Ensure $launcher_dir is in your PATH, then run: opencobolide"
fi
