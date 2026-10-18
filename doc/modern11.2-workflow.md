# modern11.2 compiler workflow

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
The existing Program/Subprogram action still selects executable/module mode.

Overrides are stored in the existing user preferences, keyed by the canonical
source path. Moving a file does not transfer its override. Return to global
settings from the same dialog. An accepted change applies on the next Compile.
Normal compilation always rebuilds to avoid retaining a binary made with old
options. Custom project build scripts continue to control their own options.

## Optional source-install launcher (Linux)

```bash
OCIDE_INSTALL_LAUNCHER=1 bash scripts/install_from_source.sh
```

Installs a launcher at `~/.local/bin/opencobolide`. Ensure `~/.local/bin` is in
PATH. `OCIDE_LAUNCHER_DIR` changes its directory. An unrelated existing command
or symlink is not overwritten. Keep the source installation and its `.venv`
in place. No sudo or system Python installation is needed. The source installer
still needs internet access for its Python dependencies.

Existing SQL preferences and their storage are unchanged. This version does not
claim to fix the unconfirmed Mageia malloc_consolidate crash.

The GixSQL build template includes `detect_sql.py`; copy it alongside `build.sh`.
Plain COBOL is compiled directly without requiring gixpp or linking libgixsql.
Embedded SQL, including SQL in COPY files, selects GixSQL preprocessing.
The detector handles standard fixed/free source and simple COPY names; it stops
on unresolved copybooks rather than silently choosing a plain build.
