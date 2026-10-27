# OpenCobolIDE 4.7.6 modern11.6

Release notes prepared **27 October 2026**.

This release brings directory-based projects, portable project and source
settings, incremental compilation, copybook handling and an IDE-owned build
workflow to the modern OpenCobolIDE continuation. It retains the original
OpenCobolIDE authorship, attribution and licence.

## New project workflow

- **New Project** creates `src`, `copybooks`, `bin`, `build`, `data` and `config`
  directories without overwriting existing project files.
- **Open Project** is available from the opening screen and File menu. It roots
  the file tree in the selected directory and opens discovered COBOL sources,
  excluding generated outputs and copybooks from compilation targets.
- Opening a file alone detects enclosing projects. One project is selected
  automatically; multiple enclosing configurations offer a project choice.
  Opening another project's file preserves the currently selected project.
- The explicitly opened project remains authoritative. An accidental nested
  `src/config/project.json` cannot redirect compilation to the wrong copybooks
  or output directory.
- **Close Project** and project switching support Save / Discard / Cancel,
  preserve unrelated standalone tabs, protect against failed saves and close
  project views across split editors and detached windows.

## Compile changed files or rebuild everything

| Action | Shortcut | Behavior |
|---|---|---|
| **Compile Project** | **Ctrl+F8** | Compiles changed sources and sources affected by changed copybooks; skips up-to-date sources. |
| **Rebuild Project** | **Ctrl+Shift+F8** | Compiles every project source, even when unchanged. |
| Compile current file | F8 | Preserves current-source compilation and existing CALL dependency detection. |
| Rebuild current file | Shift+F8 | Cleans and recompiles the current source. |

**Compile Project means compile changed files. Rebuild Project means compile all files.**

The first project build compiles everything. Subsequent builds track source
contents and recursive COPY / SQL INCLUDE dependencies. Changing a shared
copybook rebuilds its dependent sources without rebuilding unrelated sources.
Content changes are detected even when modification timestamps are preserved.

Effective compiler/settings changes, compiler or builder changes, and missing
or modified binaries/listings also trigger rebuilding. Only successful builds
with their expected outputs are recorded. A failed build invalidates previous
success and is retried; it cannot leave a false up-to-date result.

Build history is stored in `build/.ocide-build-state.json`. A missing or corrupt
history safely causes a new build. The compiler log reports skipped sources and
compiled/up-to-date counts. Unresolved or library-qualified dependencies and
legacy DBPRE/esqlOC backends are conservatively rebuilt. Source order remains
deterministic; this is copybook dependency tracking, not a new static-link target
or CALL-based build-order system.

## Portable project and per-source settings

- `config/project.json` stores shared defaults and individual source overrides.
- Effective settings follow **source → project → IDE defaults**.
- Relative paths allow projects to move between folders and computers; legacy
  IDE preferences can be migrated into project configuration.
- Controls cover compiler flags, source format, copybook paths, library paths,
  libraries, environment/tool paths, listings and GixSQL settings.
- Validation identifies conflicting formats/options, missing inputs/tools,
  duplicate output/listing destinations and settings that would overwrite inputs.
- Configuration writes are atomic. Malformed existing configurations are
  reported and preserved rather than silently replaced.

## Compiler, GixSQL and diagnostic corrections

- Project builds use the builder installed with the IDE. A project-local
  `build.sh` does not override it, and no source filename is hardcoded.
- Executable/module mode is detected per source: `PROCEDURE DIVISION USING`
  selects **`-m`**; ordinary main programs select **`-x`**, with existing explicit
  file-type overrides retained. The IDE passes its mode to the builder through
  `OCIDE_COMPILE_MODE`.
- SQL detection inspects source and copybooks. GixSQL preprocessing, include
  paths and libraries are added only for SQL builds. Plain COBOL does not require
  GixSQL. Configured copybook paths also reach SQL preprocessing.
- GnuCOBOL 3.2.0's unlabelled messages for an ignored `-I` directory no longer
  become false IDE errors. Warnings remain warnings, notes are informational,
  and verbose compiler output remains in the compiler log.
- Compiler/preprocessor exit statuses propagate correctly. Nonzero exits still
  produce an error even if the output contains only warnings; failed process
  startup returns failure. Long compilation waits for actual completion.
- These changes address the Fedora/Mageia symptom where successful compilation
  returned zero but four falsely counted errors prevented Run.

## Listings, copybooks and keyboard shortcuts

- Default listings are written to `build/{stem}.lst`; custom per-source listing
  destinations and listing settings are preserved.
- Cross references and symbols use **`--Xref -ftsymbols`**. The misspellings
  `--Xrefr` and `-Xrefr` are rejected with a correction message.
- Compiler/preprocessor/linker commands and verbose build steps are displayed.
  Background syntax checks do not overwrite build listings.
- **New File** offers `.cpy` and `.CPY`, creates an empty copybook and uses the
  project's copybook directory when appropriate. Copybooks open in the COBOL
  editor but are not standalone Compile/Run targets.
- Project, compiler-settings, listing, preferences and support actions now have
  documented shortcuts. **Help → Keyboard shortcuts** opens the reference with
  **Ctrl+Alt+H**.
- Background syntax checking uses **Ctrl+Alt+K** so the editor's Ctrl+Shift+L
  selection key remains available. The automatic listing toggle uses
  **Ctrl+Alt+G**. Existing F5, F8, Shift+F8 and standard editor keys remain.

Earlier modern improvements remain included: runtime arguments, source-format
directives, environment settings, optional diagnostic tracing, shutdown fixes and
runtime diagnostics.

## Documentation and demonstration project

The source and packages include the How-to guide, offline HTML manual and a
portable demonstration with a main program, a USING subprogram and a shared
copybook. The guides explain project settings, automatic `-x`/`-m` detection,
changed-file versus full builds, listings, SQL routing and shortcuts.

See [HOWTO_MODERN11.6.md](HOWTO_MODERN11.6.md) for the complete workflow and
shortcut table. Release collection/provenance is recorded separately in
[RELEASE_HANDOFF_MODERN11.6.md](RELEASE_HANDOFF_MODERN11.6.md).

## Tests and verification

### Automated regression results

**239 tests passed in 54.19 seconds** in the recorded final source regression
run on Linux Mint with Python 3.10 / Qt5. This includes:

- Project creation, source discovery, configuration migration, relative-path
  portability, inheritance/reset and conflict detection.
- Safe close/switch, unsaved-change choices, failed-save protection,
  split/detached views, nested configurations and standalone-file recognition.
- First-build compilation, unchanged-source skipping, preserved-timestamp
  source changes, recursive/shared copybook changes and per-source flag changes.
- Missing binaries/listings, forced rebuilding, failed project/single-file build
  retries, malformed build history, dependency cycles and duplicate candidates.
- COPY / SQL INCLUDE handling, source-format directives and comments/literals.
- Executable/module detection, plain versus SQL dispatch, listing destinations,
  cross references, compiler flags and preprocessor/compiler failure propagation.
- Warning/note/error severity, successful-build Run gating, real shortcut
  activation, shortcut collisions and copybook creation/safety.
- Existing compiler, F8, runtime-argument, help, source-installation and editor
  workflows.

An isolated **GnuCOBOL 3.2.0** compiler was also exercised without replacing
Mint's installed 3.3 development compiler. Real checks covered main `-x` and
module `-m` compilation, listings, execution, genuine compiler failure and
incremental builds after a nested copybook changed. The isolated compiler was
built without indexed-file database/curses support; those features were outside
this compatibility check.

### Collected package verification

| Target | Verification result |
|---|---|
| Debian package | Extracted successfully; all **239 shipped Python/shell files** match the application source, and the installed How-to guide matches. This file count is separate from the test count above. |
| Fedora 44 RPMs | Native binary/source RPM builds completed; rpmlint reports **0 errors, 1 warning** for the local Source0 archive URL. |
| Mageia 10 RPMs | Native binary/source RPM builds completed; rpmlint reports **0 errors, 5 warnings** for naming policy, unsigned packages and absent packager tags. |
| Source consistency | Both source RPMs contain the identical exact build-source archive. Application/build code revision: `fee4f99e3ba0533962da66963a33b837be76b198`. |
| Integrity | Supplied collection checksums verified; final publication checksums must be generated from the staged assets. |

Native package builds are confirmed. The collected build/lint logs do not by
themselves establish that every new GUI workflow passed a complete installation
acceptance test on each distribution. Source tests on Mint must not be described
as native Fedora/Mageia GUI tests. Remaining native acceptance checks are listed
in the release handoff.

### Optional SQL integration evidence

GixSQL 1.0.21dev is a separate optional component. Its builds are planned for
**separate forum publication**, not attachment as mandatory IDE dependencies.

- **Mageia 10 unified GixSQL RPM:** SQLite connection/SELECT and exit zero were
  recorded; command output confirms the main runtime loaded from
  `/usr/lib64/libgixsql.so`. The SQLite driver's exact load path was not
  independently confirmed.
- **Fedora 44:** SQLite compiled and ran through the IDE with the original split
  GixSQL packages and GnuCOBOL 3.2.0. The later unified `-2.fc44` RPM built and its
  libraries were detected, but a successful SQLite rerun after replacement was
  not explicitly confirmed.
- PostgreSQL, MySQL/MariaDB and ODBC drivers are packaged, but functional
  database tests are not confirmed.

## GitHub release assets

The planned OpenCobolIDE GitHub release attaches these **three IDE installers**:

| Platform | Asset filename |
|---|---|
| Linux Mint / Debian-family | `opencobolide_4.7.6+modern11.6_all.deb` |
| Fedora 44 | `opencobolide-4.7.6-11.6.3.fc44.noarch.rpm` |
| Mageia 10 | `opencobolide-4.7.6-11.6.3.mga10.noarch.rpm` |

The RPM packaging release is **11.6.3**; the Debian version remains
**4.7.6+modern11.6**. Retain the actual filenames and versions.

Also retain the two source RPMs, exact build-source archive, Fedora/Mageia build
kits, this release note, the How-to guide and fresh `SHA256SUMS`. The release
handoff gives their verified local locations. Documentation commits made after
package construction do not change the package code revision recorded above;
these updated release notes can be attached separately without claiming that
the older package archives already contain this revision of the notes.

## Installing over earlier Debian test builds

From the directory containing the downloaded Debian asset:

```bash
sudo apt install --reinstall --allow-downgrades ./opencobolide_4.7.6+modern11.6_all.deb
```

Earlier `+projectN` test versions sort after the consolidated plain version;
reinstall/downgrade options also replace an older package with the same version.
Verify the published checksum before installation. GnuCOBOL is required for
compilation; GixSQL is needed only for SQL projects.

## Scope and known limits

- This release continues the original OpenCobolIDE project; original attribution
  and licensing are retained.
- Native packages target **Fedora 44** and **Mageia 10**. These RPMs are not
  advertised as generic Red Hat/RPM-distribution packages.
- The internal project builder uses Bash and Linux-oriented defaults. A new
  native Windows implementation of this workflow has not been validated.
- Unresolved/unsupported dependency forms and legacy SQL backends rebuild
  conservatively rather than risk skipping necessary compilation.
- The native acceptance and optional database-driver test limits above remain
  explicit. No debugger or static-link target/build-order system is introduced.

These notes prepare the release. GitHub push, asset upload and publication have
not been performed as part of this documentation update.
