#!/bin/bash
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
target=${1:-$(cat "$script_dir/TARGET" 2>/dev/null || true)}
. /etc/os-release
case "$target" in
    fedora44)
        [[ "${ID:-}" == fedora && "${VERSION_ID:-}" == 44 ]] || { echo 'Build this kit natively on Fedora 44.' >&2; exit 1; }
        dist=.fc44 ;;
    mageia10)
        [[ "${ID:-}" == mageia && "${VERSION_ID:-}" == 10 ]] || { echo 'Build this kit natively on Mageia 10.' >&2; exit 1; }
        dist=.mga10 ;;
    *) echo 'Usage: build-rpms.sh fedora44|mageia10' >&2; exit 2 ;;
esac
for tool in rpmbuild rpmlint python3 sha256sum desktop-file-validate; do
    command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 1; }
done
(cd "$script_dir" && sha256sum -c SHA256SUMS)
python3 -c 'from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork; import pygments'
top=$(mktemp -d "${RPM_BUILD_BASE:-$HOME}/rpmbuild-modern12-${target}.XXXXXX")
output=$(mktemp -d "${RPM_OUTPUT_BASE:-$script_dir}/${target}-rpm-output.XXXXXX")
printf 'RPM build directory: %s\nResults directory: %s\n' "$top" "$output"
mkdir -p "$top"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
install -m 0644 "$script_dir"/*.tar.gz "$top/SOURCES/"
install -m 0644 "$script_dir"/*.spec "$top/SPECS/"
cp "$script_dir/SOURCE_REVISIONS.json" "$output/"
{
    cat /etc/os-release
    uname -m
    python3 --version
    rpm --version
    python3 -c 'from PyQt5.QtCore import QT_VERSION_STR, PYQT_VERSION_STR; print("Qt", QT_VERSION_STR, "PyQt", PYQT_VERSION_STR)'
} > "$output/BUILD_ENVIRONMENT.txt"
for spec in cobgdb-python.spec opencobolide-modern12.spec; do
    rpmbuild -ba --define "_topdir $top" --define "dist $dist" \
        "$top/SPECS/$spec" 2>&1 | tee "$output/rpmbuild-${spec%.spec}.log"
done
mapfile -t packages < <(find "$top/RPMS" "$top/SRPMS" -type f -name '*.rpm' -print | sort)
[[ ${#packages[@]} -eq 4 ]] || { echo 'Expected two binary and two source RPMs.' >&2; exit 1; }
for package in "${packages[@]}"; do install -m 0644 "$package" "$output/"; done
install -m 0644 "$script_dir"/*.spec "$output/"
set +e
rpmlint "${packages[@]}" 2>&1 | tee "$output/rpmlint.log"
lint_status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$lint_status" > "$output/RPMLINT_STATUS.txt"
(cd "$output" && sha256sum ./*.rpm > SHA256SUMS)
printf 'Build completed. Review native install/GUI tests and rpmlint before release: %s\n' "$output"
