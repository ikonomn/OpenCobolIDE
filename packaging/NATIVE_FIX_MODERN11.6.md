# Mageia 10 / Fedora 44 compilation fix

Changes made in the existing Mint repository, 2026-10-26.

## Cause and behavior

GnuCOBOL 3.2.0 emits two unlabelled messages for a missing `-I` directory:
`cobc: invalid parameter: -I` and `cobc: ignoring nonexistent directory ...`.
It can still compile successfully and return zero. Previously the IDE treated
both messages as errors, so compiling two plain sources counted four errors
and prevented Run. The original Fedora and Mageia traces, diagnostics and rpmlint reports were
read from the persistent USB installations; no USB files were modified.

- The internal builder and standalone GixSQL example add the GixSQL compiler
  include directory and runtime library only when source/COPY detection finds SQL.
- Ordinary project copybook paths remain available to plain builds. SQL builds
  pass configured compiler include paths to the preprocessor as well.
- Automatic executable/module selection remains unchanged.
- Explicit warnings remain warnings; notes become information. GnuCOBOL 3.2
  missing-include messages are warnings, while verbose chatter stays in the log.
- Nonzero compiler/preprocessor status is preserved. A failed build with only
  warnings still gets an error and blocks Run. Failed process startup returns
  127. Compilation waits until the process finishes, beyond Qt's default timeout.

## Fedora RPM findings

The original report contained 13 errors and 7 warnings. Packaging changes:

- Omit `.gitkeep`, `.gitignore`, Python caches from installed examples.
- Remove shebangs from non-executable Python modules and documentation scripts;
  make the internal Bash builder executable with `/bin/bash`.
- Build the source RPM using `opencobolide.spec` as its specification filename.
- Retain automatically generated PyQt5 runtime requirements; remove redundant
  Fedora `python3-qt5-base` runtime requirement (build requirement remains).
- Link duplicate licence copies to the canonical RPM licence file.
- RPM release becomes `11.6.1` to distinguish the fixed packages.

`invalid-url Source0` remains expected for the local source archive: no matching
public release URL exists yet, and publishing was deferred. Do not invent a URL
or suppress diagnostics. Replace Source0 with the verified release URL when the
user authorizes publication. Native Fedora/Mageia rebuild and rpmlint reruns
remain required; this Mint session does not claim clean native RPM results.

Mageia's original log contained zero errors and 24 warnings. Shared payload
and script changes apply there too. Its valid `Development/Other` group and
new changelog release with distribution suffix address two additional warnings.
Unsigned RPMs and missing packager identity remain expected for these local
builds; no identity or signing key was invented. Its application package name
is retained despite the generic Python library naming-policy warning.

## Verification

- Full existing regression set plus native diagnostics and UI checks:
  **216 passed in 48.64 seconds**.
- Isolated official GnuCOBOL 3.2.0 built under `/tmp` without replacing the
  installed GnuCOBOL 3.3 development compiler. Build configured without indexed
  database/curses support; these features are outside this regression.
- Real 3.2.0 main `-x` and worker `-m` builds in a path containing spaces;
  cross-reference listings and execution verified.
- Real 3.2.0 invalid COBOL build fails and produces an error diagnostic.
- Real 3.2.0 GixSQL preprocessing/linking and SQLite run:
  `DATABASE CONNECTION OK`, `SELECT RESULT: 000000001`.
- Follow-up GUI Run-gate checks: **2 passed** (warnings launch; failure blocks).
- Follow-up compiler/build/packaging checks: **30 passed**, including staging
  the Fedora cleanup commands and verifying the licence links.
- Fake tool tests cover SQL in source or nested COPY, plain mode, both -x/-m,
  compiler exits 0/9 and preprocessor exit 6.

No remote push, release upload or USB modification was performed.
