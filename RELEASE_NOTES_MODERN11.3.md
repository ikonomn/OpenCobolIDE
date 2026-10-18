# OpenCobolIDE 4.7.6+modern11.3

This diagnostic release adds an opt-in trace log for investigating the
intermittent native `malloc_consolidate()` crash reported on Mageia.

The trace records application startup, compilation, child-process launch and
completion, process state, window shutdown, Qt cleanup, and Python thread stacks
for supported fatal signals. Every event is flushed and synced immediately so
the last completed operation remains available after an abrupt abort.

Tracing is disabled by default. For a source installation, enable it with:

```bash
OCIDE_TRACE_LOG="$HOME/opencobolide-trace.jsonl" .venv/bin/opencobolide
```

Program argument values and the complete environment are not recorded. This
release gathers diagnostic evidence; it does not claim that the underlying
Mageia native-memory crash is fixed.

modern11.3 includes the automatic listing names, per-source compiler flags,
source-install launcher, runtime program arguments, and automatic plain/GixSQL
build routing introduced in modern11.2.
