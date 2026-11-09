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
# MSYS/Cygwin accept mixed drive paths, and native Python/cobc accept them too.
normalize_path() {
    case "$1" in
        [A-Za-z]:[\\/]*|\\\\*)
            if ! command -v cygpath >/dev/null; then
                printf 'Windows paths require Bash with cygpath (MSYS2 or Cygwin).\n' >&2
                return 2
            fi
            cygpath -am -- "$1"
            ;;
        *) printf '%s\n' "$1" ;;
    esac
}

project_dir=$(normalize_path "$project_dir")
source_file=$(normalize_path "$source_file")
case "$source_file" in
    /*|[A-Za-z]:/*) ;;
    *) source_file="$PWD/$source_file" ;;
esac
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
gixpp_command=$(normalize_path "$gixpp_command")
cobc_command=${COBC:-cobc}
cobc_command=$(normalize_path "$cobc_command")
gixsql_copy_dir=${GIXSQL_COPY_DIR:-/usr/share/gixsql/copy}
gixsql_copy_dir=$(normalize_path "$gixsql_copy_dir")
# An explicit IDE/environment setting wins. Otherwise locate the development
# library, leaving the compiler's native search path intact when none is found.
gixsql_library_dir=${GIXSQL_LIBRARY_DIR:-}
gixsql_library_dir=$(normalize_path "$gixsql_library_dir")
if [[ -z "$gixsql_library_dir" ]]; then
    for candidate in /usr/local/lib64 /usr/local/lib /usr/lib64 /usr/lib/*-linux-gnu /usr/lib; do
        if [[ -f "$candidate/libgixsql.so" || -f "$candidate/libgixsql.a" ]]; then
            gixsql_library_dir=$candidate
            break
        fi
    done
fi
project_copy_dir=${PROJECT_COPY_DIR:-$project_dir/copybooks}
project_copy_dir=$(normalize_path "$project_copy_dir")

command -v "$cobc_command" >/dev/null || {
    printf 'GnuCOBOL compiler not found: %s\n' "$cobc_command" >&2
    exit 127
}

program=${filename%.*}
build_dir="$project_dir/build"
bin_dir="${OCIDE_OUTPUT_DIR:-$project_dir/bin}"
bin_dir=$(normalize_path "$bin_dir")
preprocessed="$build_dir/$program.cbsql"
compile_mode=${OCIDE_COMPILE_MODE:--x}
case "$compile_mode" in
    -x) output_extension=${OCIDE_OUTPUT_EXTENSION:-} ;;
    -m) output_extension=${OCIDE_OUTPUT_EXTENSION:-.so} ;;
    *) printf 'Invalid OCIDE_COMPILE_MODE: %s\n' "$compile_mode" >&2; exit 2 ;;
esac
executable="$bin_dir/${OCIDE_OUTPUT_NAME:-$program$output_extension}"
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
            cobc_args[i+1]=$(normalize_path "${cobc_args[i+1]}")
            listing=${cobc_args[i+1]}
            has_listing=true
            ((i+=1))
            ;;
        -I|-L)
            if ((i+1 < ${#cobc_args[@]})); then
                cobc_args[i+1]=$(normalize_path "${cobc_args[i+1]}")
                ((i+=1))
            fi
            ;;
        -I*|-L*)
            cobc_args[i]="${cobc_args[i]:0:2}$(normalize_path "${cobc_args[i]:2}")"
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
    copy_path_separator=:
    case "$OSTYPE" in
        msys*|cygwin*) copy_path_separator=';' ;;
    esac
    IFS="$copy_path_separator" read -r -a environment_copy_dirs <<< "$COB_COPY_DIR"
    for directory in "${environment_copy_dirs[@]}"; do
        sql_copy_dirs+=("$(normalize_path "$directory")")
    done
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
    cobc_args+=(-I "$gixsql_copy_dir")
    if [[ -n "$gixsql_library_dir" ]]; then
        cobc_args+=(-L "$gixsql_library_dir")
    fi
    cobc_args+=(-lgixsql)
    compile_input="$preprocessed"
else
    compile_input="$source_file"
fi
# The IDE supplies reviewed/manual or automatically matched project C helpers.
c_helpers=()
c_libraries=()
if [[ -n "${OCIDE_C_SOURCES:-}" ]]; then
    helper_file=$(mktemp)
    python3 -c 'import json,os,sys; sys.stdout.buffer.write(b"".join(p.encode()+b"\0" for p in json.loads(os.environ["OCIDE_C_SOURCES"])))' > "$helper_file"
    mapfile -d '' -t c_helpers < "$helper_file"
    rm -f "$helper_file"
    for i in "${!c_helpers[@]}"; do
        c_helpers[i]=$(normalize_path "${c_helpers[i]}")
    done
fi
if [[ -n "${OCIDE_C_LIBRARIES:-}" ]]; then
    helper_file=$(mktemp)
    python3 -c 'import json,os,sys; sys.stdout.buffer.write(b"".join(p.encode()+b"\0" for p in json.loads(os.environ["OCIDE_C_LIBRARIES"])))' > "$helper_file"
    mapfile -d '' -t c_libraries < "$helper_file"
    rm -f "$helper_file"
fi
for library in "${c_libraries[@]}"; do
    present=false
    for ((i=0; i<${#cobc_args[@]}; i++)); do
        if [[ "${cobc_args[i]}" == "-l$library" ]] ||
           [[ "${cobc_args[i]}" == -l && "${cobc_args[i+1]:-}" == "$library" ]]; then present=true; break; fi
    done
    if ! "$present"; then cobc_args+=("-l$library"); fi
done
printf 'Compiling %s (%s)\n' "$compile_input" "$mode"
if [[ "${OCIDE_DEBUG_BUILD:-0}" == 1 ]]; then
    # Compile in a disposable build folder. Only matching C/header artifacts
    # are retained; object files and other intermediates are discarded.
    debug_scratch=$(mktemp -d "$build_dir/.debug-XXXXXXXX")
    debug_target=$(python3 -c 'import pathlib,sys; r=pathlib.Path(sys.argv[1]).resolve(); s=pathlib.Path(sys.argv[2]).resolve(); print((r/"debug_data"/s.relative_to(r).with_suffix("")).as_posix())' "$project_dir" "$source_file")
    # Deduplicate only the debug switches, preserving other compiler arguments.
    unique_args=()
    debug_seen=' '
    argument_value=false
    for flag in "${cobc_args[@]}"; do
        if "$argument_value"; then
            unique_args+=("$flag"); argument_value=false; continue
        fi
        case "$flag" in
            -A|-Q|-I|-L|-l|-T|-t|-o) argument_value=true ;;
            -g|-fsource-location|-ftraceall|-save-temps)
                if [[ "$debug_seen" == *" $flag "* ]]; then continue; fi
                debug_seen+="$flag " ;;
        esac
        unique_args+=("$flag")
    done
    cobc_args=("${unique_args[@]}")
    # Preserve explicit optimization; use -O0 only as the debug default.
    has_optimization=false
    for flag in "${cobc_args[@]}"; do
        case "$flag" in -O|-O[0-9]*|-Os|-Oz|-Og|-Ofast) has_optimization=true ;; esac
    done
    if ! "$has_optimization"; then cobc_args+=(-O0); fi
    for flag in -g -fsource-location -ftraceall -save-temps; do
        present=false
        for existing in "${cobc_args[@]}"; do
            if [[ "$existing" == "$flag" ]]; then present=true; break; fi
        done
        if ! "$present"; then cobc_args+=("$flag"); fi
    done
    printf 'Debug compilation enabled; explicit optimization flags are preserved.\n'
    run_logged bash -c 'cd "$1"; shift; exec "$@"' _ "$debug_scratch" \
        "$cobc_command" "${cobc_args[@]}" \
        -A "-fdebug-prefix-map=$debug_scratch=$debug_target" \
        -o "$executable" "$compile_input" "${c_helpers[@]}"
    mkdir -p "$debug_target"
    find "$debug_target" -maxdepth 1 -type f \( -name '*.c' -o -name '*.h' \) -delete
    find "$debug_scratch" -maxdepth 1 -type f \( -name '*.c' -o -name '*.h' \) -exec cp -- {} "$debug_target/" \;
    printf 'Debug C sources and headers: %s\n' "$debug_target"
else
    run_logged "$cobc_command" "${cobc_args[@]}" -o "$executable" "$compile_input" "${c_helpers[@]}"
fi

printf 'Output:     %s\n' "$executable"
if [[ "${OCIDE_GENERATE_LISTING:-1}" == 1 ]]; then
    printf 'Listing:    %s\n' "$listing"
fi
