#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
project_root="$(cd "$script_dir/../.." && pwd)"
version="4.7.6-modern11.5"
source_name="opencobolide-${version}.tar.gz"
kit_name="opencobolide-modern11.5-mageia10-build-kit"
output_dir="${OCIDE_KIT_OUTPUT_DIR:-$project_root/dist}"
working_dir="$(mktemp -d "${TMPDIR:-/tmp}/ocide-mageia-kit.XXXXXX")"

cleanup() {
    rm -rf "$working_dir"
}
trap cleanup EXIT

if ! git -C "$project_root" diff --quiet --ignore-submodules -- || \
        ! git -C "$project_root" diff --cached --quiet --ignore-submodules --; then
    echo "Error: commit the intended source changes before creating the kit." >&2
    exit 1
fi

mkdir -p "$working_dir/$kit_name" "$output_dir"

git -C "$project_root" archive \
    --format=tar.gz \
    --prefix="OpenCobolIDE-${version}/" \
    -o "$working_dir/$kit_name/$source_name" \
    HEAD

install -m 0644 "$script_dir/opencobolide-modern11.5.spec" \
    "$working_dir/$kit_name/"
install -m 0755 "$script_dir/build-mageia10-rpm.sh" \
    "$working_dir/$kit_name/"
install -m 0644 "$script_dir/README.md" \
    "$working_dir/$kit_name/README.md"

tar -C "$working_dir" -czf "$output_dir/$kit_name.tar.gz" "$kit_name"
sha256sum "$output_dir/$kit_name.tar.gz"
