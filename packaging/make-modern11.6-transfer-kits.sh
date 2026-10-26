#!/bin/bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
output=${1:?Usage: make-modern11.6-transfer-kits.sh OUTPUT_DIRECTORY}
mkdir -p "$output"
output=$(cd "$output" && pwd)
# Every kit must use the exact committed source, not an uncommitted mixture.
if [[ -n "$(git -C "$repo" status --porcelain --untracked-files=no)" ]]; then
    echo 'Commit tracked source changes before producing the transfer kits.' >&2
    exit 1
fi
revision=$(git -C "$repo" rev-parse HEAD)
archive="$output/opencobolide-4.7.6-modern11.6.tar.gz"
git -C "$repo" archive --format=tar.gz --prefix=OpenCobolIDE-4.7.6-modern11.6/ HEAD > "$archive"
printf '%s\n' "$revision" > "$output/SOURCE_REVISION.txt"
for target in mageia10 fedora44; do
    kit="$output/opencobolide-modern11.6-$target-kit"
    if [[ -e "$kit" ]]; then echo "Kit directory already exists: $kit" >&2; exit 1; fi
    mkdir -p "$kit"
    if [[ "$target" == mageia10 ]]; then folder=mageia; script=build-mageia10-rpm.sh; else folder=fedora; script=build-fedora44-rpm.sh; fi
    install -m 0644 "$archive" "$kit/"
    install -m 0644 "$repo/packaging/$folder/opencobolide-modern11.6.spec" "$kit/"
    install -m 0755 "$repo/packaging/$folder/$script" "$kit/"
    install -m 0644 "$repo/packaging/RPM_MODERN11.6.md" "$kit/README.md"
    install -m 0644 "$output/SOURCE_REVISION.txt" "$kit/"
    (cd "$kit" && sha256sum *.tar.gz *.spec *.sh README.md SOURCE_REVISION.txt > SHA256SUMS)
    tar -C "$output" -czf "$output/opencobolide-modern11.6-$target-kit.tar.gz" "$(basename "$kit")"
done
(cd "$output" && sha256sum opencobolide*.tar.gz > TRANSFER_SHA256SUMS)
echo "Transfer kits ready at $output for source $revision"
