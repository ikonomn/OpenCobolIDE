# modern11.4 Linux service release

## Shutdown lifecycle correction

OpenCobolIDE now keeps its Python references alive until the Qt event loop has
returned. Application cleanup runs once after `app.exec_()` and is idempotent.
This avoids destroying Python wrappers while their C++ Qt objects are still
participating in shutdown.

The correction applies to every supported Linux source installation and to the
Debian-family package. It was identified from a Mageia 10 trace using Python
3.13, Qt 5.15, Wayland and glibc 2.42, but it improves lifecycle correctness on
other Linux distributions and desktop sessions as well.

## Native crash trace

Tracing remains optional and disabled during normal use:

```bash
OCIDE_TRACE_LOG="$HOME/opencobolide-trace.jsonl" .venv/bin/opencobolide
```

Each trace event is synced to disk. Program argument values and the complete
environment are not recorded.

## Compiler workflow

modern11.4 retains automatic listing filenames, per-source compiler flags,
runtime program arguments, the optional source-install launcher, and automatic
plain COBOL/GixSQL build routing from modern11.2 and modern11.3.

Enable **COBOL → Automatic listing filename** to name a listing after its
source. Use **COBOL → Compiler options for this file…** for a source-specific
replacement of the global extra flags.
