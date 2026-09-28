#!/usr/bin/env bash
set -euo pipefail

# Generic project build script for OpenCobolIDE + GixSQL.
# Copy this file to the root of a COBOL project and make it executable.

project_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source_file=${1:-}

if [[ -z "$source_file" ]]; then
    printf 'Usage: %s FILE.cbl|FILE.cob\n' "${0##*/}" >&2
    exit 2
fi
if [[ "$source_file" != /* ]]; then
    source_file="$PWD/$source_file"
fi
if [[ ! -f "$source_file" ]]; then
    printf 'Source file not found: %s\n' "$source_file" >&2
    exit 2
fi

filename=${source_file##*/}
extension=${filename##*.}
extension=${extension,,}
if [[ "$extension" != "cbl" && "$extension" != "cob" ]]; then
    printf 'Expected a .cbl or .cob source: %s\n' "$source_file" >&2
    exit 2
fi

gixpp_command=${GIXPP:-gixpp}
cobc_command=${COBC:-cobc}
gixsql_copy_dir=${GIXSQL_COPY_DIR:-/usr/share/gixsql/copy}
gixsql_library_dir=${GIXSQL_LIBRARY_DIR:-/usr/lib}
project_copy_dir=${PROJECT_COPY_DIR:-$project_dir/copybooks}

command -v "$gixpp_command" >/dev/null || {
    printf 'GixSQL preprocessor not found: %s\n' "$gixpp_command" >&2
    exit 127
}
command -v "$cobc_command" >/dev/null || {
    printf 'GnuCOBOL compiler not found: %s\n' "$cobc_command" >&2
    exit 127
}

program=${filename%.*}
build_dir="$project_dir/build"
bin_dir="$project_dir/bin"
preprocessed="$build_dir/$program.cbsql"
executable="$bin_dir/$program"
listing="$build_dir/$program.lst"

mkdir -p "$build_dir" "$bin_dir"

gixpp_args=(-e -S -z a -P varchar -I "$gixsql_copy_dir")
cobc_args=(-x -v -debug --Xref -ftsymbols -T "$listing"
    -I "$gixsql_copy_dir" -L "$gixsql_library_dir" -lgixsql)
if [[ -d "$project_copy_dir" ]]; then
    gixpp_args+=(-I "$project_copy_dir")
    cobc_args+=(-I "$project_copy_dir")
fi

printf 'Preprocessing %s\n' "$source_file"
"$gixpp_command" "${gixpp_args[@]}" \
    -i "$source_file" -o "$preprocessed"

printf 'Compiling %s\n' "$preprocessed"
"$cobc_command" "${cobc_args[@]}" \
    -o "$executable" "$preprocessed"

printf 'Executable: %s\n' "$executable"
printf 'Listing:    %s\n' "$listing"
