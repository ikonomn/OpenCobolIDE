#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
spec_file="${OCIDE_SPEC_FILE:-$script_dir/opencobolide-modern11.6.spec}"
source_file="${OCIDE_SOURCE_FILE:-$script_dir/opencobolide-4.7.6-modern11.6.tar.gz}"
top_dir="${OCIDE_RPM_TOPDIR:-$HOME/rpmbuild}"
output_dir="${OCIDE_RPM_OUTPUT:-$script_dir/mageia10-rpm-output}"

if [ ! -r /etc/mageia-release ]; then
    echo "Error: this package must be built and tested on Mageia 10." >&2
    exit 1
fi

if ! grep -qE 'Mageia release 10([[:space:]]|$)' /etc/mageia-release; then
    echo "Error: Mageia 10 was not detected:" >&2
    cat /etc/mageia-release >&2
    exit 1
fi

for command_name in rpmbuild rpmspec rpmdev-setuptree rpmlint python3; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "Error: required command is missing: $command_name" >&2
        echo "Install task-packager and the dependencies from the instructions." >&2
        exit 1
    fi
done

if [ ! -f "$spec_file" ]; then
    echo "Error: spec file not found: $spec_file" >&2
    exit 1
fi

if [ ! -f "$source_file" ]; then
    echo "Error: source archive not found: $source_file" >&2
    exit 1
fi

python3 -c 'from PyQt5 import QtCore, QtGui, QtWidgets, QtNetwork'
python3 -c 'import pygments'

rpmdev-setuptree
mkdir -p "$top_dir/SOURCES" "$top_dir/SPECS" "$output_dir"
install -m 0644 "$source_file" "$top_dir/SOURCES/"
install -m 0644 "$spec_file" "$top_dir/SPECS/opencobolide.spec"

rpmbuild -ba \
    --define "_topdir $top_dir" \
    "$top_dir/SPECS/opencobolide.spec" 2>&1 | tee "$output_dir/rpmbuild.log"

rpm_version=$(rpmspec -q --srpm --qf '%{VERSION}' "$spec_file")
rpm_release=$(rpmspec -q --srpm --qf '%{RELEASE}' "$spec_file")
mapfile -t packages < <(
    find "$top_dir/RPMS" "$top_dir/SRPMS" \
        -type f -iname "opencobolide-${rpm_version}-${rpm_release}*.rpm" -print | sort
)

if [ "${#packages[@]}" -lt 2 ]; then
    echo "Error: the expected binary and source RPMs were not found." >&2
    exit 1
fi

for package in "${packages[@]}"; do
    install -m 0644 "$package" "$output_dir/"
done

set +e
rpmlint "${packages[@]}" 2>&1 | tee "$output_dir/rpmlint.log"
rpmlint_status="${PIPESTATUS[0]}"
set -e
(cd "$output_dir" && sha256sum ./*.rpm > SHA256SUMS)

echo
echo "Mageia 10 RPM build completed."
echo "Results: $output_dir"
echo "rpmlint exit status: $rpmlint_status (see rpmlint.log)"

collector="$script_dir/release_bundle.py"
[[ -f "$collector" ]] || collector="$script_dir/../../scripts/release_bundle.py"
source_root="$script_dir"
if [[ -d "$script_dir/../../.git" ]]; then source_root=$(cd "$script_dir/../.." && pwd); fi
transfer_history=()
for file in "$script_dir"/*.bundle "$script_dir"/SOURCE_REVISION.txt; do
    if [[ -f "$file" ]]; then transfer_history+=("$file"); fi
done
python3 "$collector" --system mageia10 --app opencobolide \
    --output "${RELEASE_OUTPUT_BASE:-$script_dir}" --source "$source_root" \
    --files "${packages[@]}" "${transfer_history[@]}" "$source_file" "$spec_file" "$script_dir/build-mageia10-rpm.sh" "$output_dir"/*.log
