# modern11.3 compiler and diagnostics workflow

## Automatic listings

Enable **COBOL → Automatic listing filename** to write `payapply1.prn` when
compiling `payapply1.cbl`. Listings are written relative to the source directory.
The option is off by default. An explicit `-T custom.prn` or `-t custom.prn`
keeps its filename. A bare `-T` or `-t` uses the source basename; `{stem}` in a
listing filename is replaced by that basename. Syntax checking does not produce
listings. A project with a custom `build.sh` controls its own listing options.

## Per-file compiler flags

Open a saved file and choose **COBOL → Compiler options for this file…**.
Choose global defaults or custom flags. Custom flags replace the global extra
flags; an empty custom value means no extra flags. Standard, source format,
copybook paths, libraries and SQL preferences retain their shared settings.

## Optional source-install launcher (Linux)

```bash
OCIDE_INSTALL_LAUNCHER=1 bash scripts/install_from_source.sh
```

The launcher is installed at `~/.local/bin/opencobolide`. Keep the source
installation and its `.venv` in place.

## Native crash trace

Tracing is disabled during normal use. To investigate an intermittent native
crash, start the source installation with:

```bash
OCIDE_TRACE_LOG="$HOME/opencobolide-trace.jsonl" .venv/bin/opencobolide
```

The trace records startup, compilation, program launch and completion, child
process state, window shutdown and Qt cleanup. Each event is synced to disk so
the last completed step remains available after an abrupt abort. Python fault
stacks are written to the same file for supported fatal signals. Program
argument values and the complete environment are not recorded.

This diagnostic logging does not claim to fix the unconfirmed Mageia
`malloc_consolidate()` crash. It provides evidence to locate the failing stage.

The GixSQL build template includes `detect_sql.py`; copy it alongside `build.sh`.
Plain COBOL is compiled directly. Embedded SQL, including SQL in COPY files,
selects GixSQL preprocessing.
