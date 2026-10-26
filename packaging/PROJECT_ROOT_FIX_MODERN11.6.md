# Project-root and copybook validation fix — RPM 11.6.2

The Fedora 44 screenshot showed SQL/COPY validation failing for both sources.
Inspection of a read-only copy from Fedora persistent storage revealed two
configuration files: `config/project.json` and `src/config/project.json`.
Nearest-config discovery selected `src`, losing the parent's copybooks,
source settings and output paths even when the parent was opened in the IDE.

The explicitly opened project now owns its contained sources for the session.
Closing or switching projects clears/changes that selection. The editor sends
the selected root to its background syntax checker as request context. Standalone files
still use nearest-config discovery; deliberately opening the nested project
still selects it. No nested configuration is deleted or rewritten.

Validation also includes the builder's implicit `project/copybooks` path, even
when configured paths are empty, inherited, or project defaults disabled.
`PROJECT_COPY_DIR` overrides are respected. Missing copybooks remain errors,
and SQL inside copybooks still requires the SQL tools.

Opening a file on its own now discovers enclosing project configurations.
With one project it opens that project and focuses the requested file, preserving
unrelated tabs. With multiple enclosing configurations it asks which project to
open. A file belonging to a different project does not silently switch an already
opened project; a status message identifies its owner.

## Distribution checks

This is shared IDE code used by Mint, Mageia 10 and Fedora 44. Both RPM
specifications now use release **11.6.2**; the Debian source uses the same fix.
Copies of the actual Mint and Fedora projects were validated, compiled and run
on Mint. The Fedora project retained its nested src configuration during this
check. Original projects and USB files were not modified.

Mageia's new package has **not** been built/tested by the user yet. Its persistent
USB is not currently mounted in this session. Native Fedora/Mageia installation
and GUI retests remain pending; host-side tests are not native distribution tests.

Open the intended top-level project folder, compile both sources, then run the
main program. Verify binaries in top-level bin/, cross-reference listings in
build/, no SQL tooling for this plain project, and correct -x/-m detection.

## Verification

- Final complete regression suite, including single-file detection:
  **229 passed in 40.25 seconds**.
- Single-file detection, project lifecycle and settings checks: **78 passed**.
- Eight copybook validation cases cover inherited/empty/disabled settings,
  SQL-containing copybooks, genuinely missing COPYs and PROJECT_COPY_DIR.
- Nested-config GUI regression verifies parent selection, compilation/listing
  locations, unchanged nested configuration, Close Project and explicit nested
  project selection.
- Mint and Fedora saved-project copies compile and run on the Mint host.
- Compiler 3.2.0 coverage retained from the native build fix.
- Both native RPM kits are generated from the same committed source and include
  checksums. They are source/build kits, not prebuilt or native-tested RPMs.
