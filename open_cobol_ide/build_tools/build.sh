#!/usr/bin/env bash
set -euo pipefail

# Generic project build script for OpenCobolIDE + GixSQL.
# Installed with the IDE. Project-local scripts are never executed.

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
project_dir=${OCIDE_PROJECT_DIR:?The IDE must supply the project directory}
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
if [[ "$extension" != "cbl" && "$extension" != "cob" && "$extension" != "pco" ]]; then
    printf 'Expected a .cbl or .cob source: %s\n' "$source_file" >&2
    exit 2
fi

gixpp_command=${GIXPP:-gixpp}
cobc_command=${COBC:-cobc}
gixsql_copy_dir=${GIXSQL_COPY_DIR:-/usr/share/gixsql/copy}
gixsql_library_dir=${GIXSQL_LIBRARY_DIR:-/usr/lib}
project_copy_dir=${PROJECT_COPY_DIR:-$project_dir/copybooks}

command -v "$cobc_command" >/dev/null || {
    printf 'GnuCOBOL compiler not found: %s\n' "$cobc_command" >&2
    exit 127
}

program=${filename%.*}
build_dir="$project_dir/build"
bin_dir="$project_dir/bin"
preprocessed="$build_dir/$program.cbsql"
compile_mode=${OCIDE_COMPILE_MODE:--x}
case "$compile_mode" in
    -x) output_extension=${OCIDE_OUTPUT_EXTENSION:-} ;;
    -m) output_extension=${OCIDE_OUTPUT_EXTENSION:-.so} ;;
    *) printf 'Invalid OCIDE_COMPILE_MODE: %s\n' "$compile_mode" >&2; exit 2 ;;
esac
executable="$bin_dir/$program$output_extension"
listing="$build_dir/$program.lst"

mkdir -p "$build_dir" "$bin_dir"

run_logged() {
    printf '$ '
    printf '%q ' "$@"
    printf '\n'
    "$@"
}

flags_file=''
debug_scratch=''
cleanup() {
    [[ -z "$flags_file" ]] || rm -f "$flags_file"
    [[ -z "$debug_scratch" ]] || rm -rf "$debug_scratch"
    return 0
}
trap cleanup EXIT
cobc_args=("$compile_mode")
if [[ -n "${OCIDE_COMPILER_FLAGS+x}" ]]; then
    flags_file=$(mktemp)
    python3 -c 'import json, os, sys; flags=json.loads(os.environ["OCIDE_COMPILER_FLAGS"]); sys.stdout.buffer.write(b"".join(f.encode()+b"\0" for f in flags))' > "$flags_file"
    mapfile -d '' -t ide_flags < "$flags_file"
    cobc_args+=("${ide_flags[@]}")
else
    cobc_args+=(-debug --Xref -ftsymbols)
fi
# IDE flags replace extra compiler flags, but retain a default listing and
# verbose build diagnostics unless the user supplied a custom listing.
has_listing=false
has_verbose=false
has_xref=false
has_symbols=false
for ((i=0; i<${#cobc_args[@]}; i++)); do
    case "${cobc_args[i]}" in
        -T|-t)
            if ((i+1 >= ${#cobc_args[@]})); then
                printf 'Listing option requires a filename\n' >&2
                exit 2
            fi
            listing=${cobc_args[i+1]}
            has_listing=true
            ((i+=1))
            ;;
        -v|--verbose) has_verbose=true ;;
        -X|--Xref) has_xref=true ;;
        -ftsymbols) has_symbols=true ;;
    esac
done
if [[ "${OCIDE_GENERATE_LISTING:-1}" == 1 ]] && ! "$has_listing"; then
    cobc_args+=(-T "$listing")
fi
if [[ "${OCIDE_GENERATE_LISTING:-1}" == 1 ]] && ! "$has_xref"; then
    cobc_args+=(--Xref)
fi
if [[ "${OCIDE_GENERATE_LISTING:-1}" == 1 ]] && ! "$has_symbols"; then
    cobc_args+=(-ftsymbols)
fi
if ! "$has_verbose"; then
    cobc_args+=(-v)
fi
gixpp_args=(-e -S -z a -P varchar -I "$gixsql_copy_dir")
if [[ -d "$project_copy_dir" ]]; then
    gixpp_args+=(-I "$project_copy_dir")
    cobc_args+=(-I "$project_copy_dir")
fi

# Include IDE/project/source copybook paths in SQL dependency discovery too.
sql_copy_dirs=("$project_copy_dir" "$gixsql_copy_dir")
if [[ -n "${COB_COPY_DIR:-}" ]]; then
    IFS=: read -r -a environment_copy_dirs <<< "$COB_COPY_DIR"
    sql_copy_dirs+=("${environment_copy_dirs[@]}")
fi
for ((i=0; i<${#cobc_args[@]}; i++)); do
    case "${cobc_args[i]}" in
        -I) ((i+=1)); sql_copy_dirs+=("${cobc_args[i]}"); gixpp_args+=(-I "${cobc_args[i]}") ;;
        -I*) sql_copy_dirs+=("${cobc_args[i]:2}"); gixpp_args+=(-I "${cobc_args[i]:2}") ;;
    esac
done
printf 'Source: %s\nCompile mode: %s\n' "$source_file" "$compile_mode"
printf 'Checking source and copybooks for SQL...\n'
mode=$(python3 "$script_dir/detect_sql.py" "$source_file" "${sql_copy_dirs[@]}")
printf 'SQL detection: %s\n' "$mode"

if [[ "$mode" == "sql" ]]; then
    command -v "$gixpp_command" >/dev/null || {
        printf 'GixSQL preprocessor not found: %s\n' "$gixpp_command" >&2
        exit 127
    }
    printf 'Preprocessing %s\n' "$source_file"
    run_logged "$gixpp_command" "${gixpp_args[@]}" \
        -i "$source_file" -o "$preprocessed"
    cobc_args+=(-I "$gixsql_copy_dir" -L "$gixsql_library_dir" -lgixsql)
    compile_input="$preprocessed"
else
    compile_input="$source_file"
fi
printf 'Compiling %s (%s)\n' "$compile_input" "$mode"
if [[ "${OCIDE_DEBUG_BUILD:-0}" == 1 ]]; then
    # Compile in a disposable build folder. Only matching C/header artifacts
    # are retained; object files and other intermediates are discarded.
    debug_scratch=$(mktemp -d "$build_dir/.debug-XXXXXXXX")
    debug_target=$(python3 -c 'import pathlib,sys; r=pathlib.Path(sys.argv[1]).resolve(); s=pathlib.Path(sys.argv[2]).resolve(); print(r/"debug_data"/s.relative_to(r).with_suffix(""))' "$project_dir" "$source_file")
    run_logged bash -c 'cd "$1"; shift; exec "$@"' _ "$debug_scratch" \
        "$cobc_command" "${cobc_args[@]}" -g -fsource-location -ftraceall -O0 -save-temps \
        -A "-fdebug-prefix-map=$debug_scratch=$debug_target" \
        -o "$executable" "$compile_input"
    mkdir -p "$debug_target"
    find "$debug_target" -maxdepth 1 -type f \( -name '*.c' -o -name '*.h' \) -delete
    find "$debug_scratch" -maxdepth 1 -type f \( -name '*.c' -o -name '*.h' \) -exec cp -- {} "$debug_target/" \;
    printf 'Debug C sources and headers: %s\n' "$debug_target"
else
    run_logged "$cobc_command" "${cobc_args[@]}" -o "$executable" "$compile_input"
fi

printf 'Output:     %s\n' "$executable"
if [[ "${OCIDE_GENERATE_LISTING:-1}" == 1 ]]; then
    printf 'Listing:    %s\n' "$listing"
fi
