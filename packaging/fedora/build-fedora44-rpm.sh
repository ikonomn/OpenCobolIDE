#!/bin/bash
set -euo pipefail
script_dir=$(cd "$(dirname "$0")" && pwd)
spec_file=${OCIDE_SPEC_FILE:-$script_dir/opencobolide-modern11.6.spec}
source_file=${OCIDE_SOURCE_FILE:-$script_dir/opencobolide-4.7.6-modern11.6.tar.gz}
top_dir=${OCIDE_RPM_TOPDIR:-$HOME/rpmbuild-opencobolide-modern11.6-fedora44}
output_dir=${OCIDE_RPM_OUTPUT:-$script_dir/fedora44-rpm-output}
# A native Fedora 44 build is required; do not relabel an RPM built on Mint.
. /etc/os-release
if [[ "${ID:-}" != fedora || "${VERSION_ID:-}" != 44 ]]; then
    echo 'Error: build and test this package on Fedora 44.' >&2
    exit 1
fi
for command_name in rpmbuild rpmlint python3 sha256sum; do
    command -v "$command_name" >/dev/null || { echo "Missing command: $command_name" >&2; exit 1; }
done
[[ -f "$source_file" && -f "$spec_file" ]] || { echo 'Missing source archive or spec.' >&2; exit 1; }
python3 -c 'from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork; import pygments'
mkdir -p "$top_dir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS} "$output_dir"
install -m 0644 "$source_file" "$top_dir/SOURCES/"
install -m 0644 "$spec_file" "$top_dir/SPECS/opencobolide.spec"
rpmbuild -ba --define "_topdir $top_dir" --define 'dist .fc44' \
    "$top_dir/SPECS/opencobolide.spec" 2>&1 | tee "$output_dir/rpmbuild.log"
mapfile -t packages < <(find "$top_dir/RPMS" "$top_dir/SRPMS" \
    -type f -name 'opencobolide-4.7.6-11.6*.rpm' -print | sort)
[[ ${#packages[@]} -ge 2 ]] || { echo 'Expected binary and source RPMs were not found.' >&2; exit 1; }
for package in "${packages[@]}"; do install -m 0644 "$package" "$output_dir/"; done
set +e
rpmlint "${packages[@]}" 2>&1 | tee "$output_dir/rpmlint.log"
lint_status=${PIPESTATUS[0]}
set -e
(cd "$output_dir" && sha256sum ./*.rpm > SHA256SUMS)
printf 'Fedora 44 RPM build complete. Results: %s\nrpmlint status: %s\n' "$output_dir" "$lint_status"
