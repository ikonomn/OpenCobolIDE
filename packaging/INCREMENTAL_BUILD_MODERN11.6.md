# Changed-file compilation and keyboard shortcuts — RPM 11.6.3

**Compile Project (Ctrl+F8) compiles changed files.** It rebuilds a source when
its contents, recursively used COPY/SQL INCLUDE files, effective settings or
compiler/builder change. Missing or modified binaries/listings also rebuild.
Unchanged sources are skipped and reported in the compiler log.

**Rebuild Project (Ctrl+Shift+F8) compiles all files**, even unchanged ones.
**F8 and Shift+F8 retain their current-file behavior.**

Build history is local, under `build/.ocide-build-state.json`. Only successful
builds with their expected outputs are recorded. Forced failed rebuilds invalidate
previous success, so the next Compile Project retries them. Corrupt/missing
history causes a fresh build. Content changes are detected even when source
modification times are preserved. Ambiguous copybook search paths track all
matching candidates conservatively; unresolved/library-qualified dependencies
and legacy SQL backends are always rebuilt.

The How-to guide, RST source manual and installed HTML manual explain the
changed/all distinction and contain the shortcut table. Help → Keyboard shortcuts
(Ctrl+Alt+H) lists project, compiler settings, listing, preference and support
commands. Ctrl+Alt+K toggles background syntax checking, avoiding the existing
Ctrl+Shift+L editor-selection key. Existing F8/F5 and editor shortcuts remain.
The automatic listing toggle uses Ctrl+Alt+G, avoiding the common desktop lock
shortcut Ctrl+Alt+L.

## Verification

- Full regression suite: **239 passed in 54.19 seconds**.
- Actual compilation tests cover first build, no-change skip, source changes
  with preserved timestamps, shared/nested copybook changes, per-source flag
  changes, missing listing/binary, forced rebuild, failed forced rebuild retry,
  corrupt cache and unchanged-source F8 behavior.
- Dependency tests cover SQL INCLUDE, cycles, duplicate candidates and format
  directives in comments/literals.
- GUI tests verify shortcut uniqueness, actual Ctrl+F8/Ctrl+Shift+F8 dispatch,
  unchanged F8/Shift+F8 keys, disabled Rebuild Project without a project, and
  copybook safety for program-type overrides.
- GnuCOBOL 3.2.0 compile/run coverage retained, plus real incremental first-build,
  skip and changed-nested-copybook rebuild checks.

These are shared IDE changes for Mint, Mageia 10 and Fedora 44. Updated source
kits use RPM release 11.6.3. Native RPM rebuild, rpmlint and installation testing
on each USB installation are still required. No remote publication is performed.
